#!/usr/bin/env python3
# DESIGN DECISION AUTOSAVE — Persist theme/token/primitive edits to a local Obsidian-style vault
# Alex Hale (2026-04-14)
# PostToolUse hook on Edit|Write
#
# Auto-saves design-system-relevant file changes (tailwind.config, components.json,
# globals.css, tokens.json, components/ui/*, .interface-design/system.md) to
# ~/vault/decisions/ as append-only markdown entries.

import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime

TRIGGER_PATTERNS = [
    re.compile(r'tailwind\.config\.(ts|js|cjs|mjs)$'),
    re.compile(r'components\.json$'),
    re.compile(r'(globals|app|index)\.css$'),
    re.compile(r'tokens\.json$'),
    re.compile(r'\.interface-design/system\.md$'),
    re.compile(r'/components/ui/[^/]+\.tsx$'),
    re.compile(r'design-library\.json$'),
]

DECISIONS_DIR = os.path.expanduser('~/vault/decisions')
HASH_STORE = os.path.expanduser('~/.claude/sensory-memory/autosave-hashes.json')
MAX_INPUT_BYTES = 50_000


def find_project_root(start_path):
    """Walk up from start_path to find package.json or CLAUDE.md. Return (root, slug)."""
    p = os.path.dirname(os.path.abspath(start_path))
    home = os.path.expanduser('~')
    while p and p != '/' and p != home:
        if os.path.exists(os.path.join(p, 'package.json')) or os.path.exists(os.path.join(p, 'CLAUDE.md')):
            return p, os.path.basename(p)
        p = os.path.dirname(p)
    return None, 'unknown'


def _load_hashes() -> dict:
    try:
        with open(HASH_STORE, 'r', encoding='utf-8') as f:
            return json.load(f) or {}
    except Exception:
        return {}


def _save_hashes(d: dict) -> None:
    try:
        os.makedirs(os.path.dirname(HASH_STORE), exist_ok=True)
        with open(HASH_STORE, 'w', encoding='utf-8') as f:
            json.dump(d, f)
    except Exception:
        pass


def main() -> int:
    tool_name = os.environ.get('CLAUDE_TOOL_NAME', '')
    tool_input = os.environ.get('CLAUDE_TOOL_INPUT', '{}')

    if tool_name not in ('Edit', 'Write'):
        return 0

    # Size guard on raw tool input — abandon absurdly large payloads early.
    if len(tool_input) > MAX_INPUT_BYTES:
        return 0

    try:
        input_data = json.loads(tool_input)
        file_path = input_data.get('file_path', '')
    except Exception:
        return 0

    if not file_path:
        return 0

    # Match against trigger patterns
    trigger_name = None
    for pat in TRIGGER_PATTERNS:
        if pat.search(file_path):
            trigger_name = pat.pattern
            break
    if not trigger_name:
        return 0

    if not os.path.exists(file_path):
        return 0

    # Detect project root
    project_root, project_slug = find_project_root(file_path)

    # Read file (truncate if huge)
    try:
        file_size = os.path.getsize(file_path)
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            if file_size > 100 * 1024:
                content_lines = []
                for i, line in enumerate(f):
                    if i >= 50:
                        break
                    content_lines.append(line)
                excerpt = ''.join(content_lines) + f'\n... (truncated at 50 lines of {file_size // 1024}KB)'
            else:
                excerpt = f.read()
    except Exception:
        excerpt = '(could not read file)'

    # Cap excerpt
    excerpt_lines = excerpt.split('\n')
    if len(excerpt_lines) > 20:
        excerpt = '\n'.join(excerpt_lines[:20]) + f'\n... ({len(excerpt_lines) - 20} more lines)'

    # Get git diff
    diff = '(not a git repo)'
    if project_root and os.path.exists(os.path.join(project_root, '.git')):
        try:
            result = subprocess.run(
                ['git', '-C', project_root, 'diff', '--', file_path],
                capture_output=True, text=True, timeout=3
            )
            if result.returncode == 0 and result.stdout:
                diff = result.stdout[:2000]
            elif result.returncode == 0:
                diff = '(no uncommitted changes — file at HEAD)'
        except Exception:
            diff = '(git diff timeout or error)'

    # Build entry
    now = datetime.now()
    date_str = now.strftime('%Y-%m-%d')
    time_str = now.strftime('%H:%M')
    rel_path = os.path.relpath(file_path, project_root) if project_root else file_path

    # Sanitize slug — strip anything not [a-z0-9_-], collapse repeats, cap length
    safe_slug = re.sub(r'[^a-z0-9_-]+', '-', project_slug.lower()).strip('-')[:64] or 'unknown'

    os.makedirs(DECISIONS_DIR, exist_ok=True)
    decisions_path = os.path.join(DECISIONS_DIR, f'{date_str}-design-{safe_slug}.md')

    # Realpath assertion — guard against symlink/traversal escape from DECISIONS_DIR
    real_root = os.path.realpath(DECISIONS_DIR)
    real_target = os.path.realpath(decisions_path)
    if not (real_target == real_root or real_target.startswith(real_root + os.sep)):
        return 0

    # Write frontmatter only if new file. Use safe_slug everywhere — raw project_slug
    # could contain newlines/brackets that break YAML frontmatter parsing downstream.
    if not os.path.exists(decisions_path):
        frontmatter = f'''---
date: {date_str}
type: decision
project: {safe_slug}
tags: [memory, decision, design, {safe_slug}]
---

# Design Decisions — {safe_slug} — {date_str}

'''
        try:
            with open(decisions_path, 'w', encoding='utf-8') as f:
                f.write(frontmatter)
        except Exception:
            return 0

    # Content-hash dedup: if (rel_path, diff, excerpt) matches the last hash
    # written for this decisions file, skip re-appending.
    content_hash = hashlib.sha256(
        (rel_path + '\x1f' + diff + '\x1f' + excerpt).encode('utf-8', errors='replace')
    ).hexdigest()
    hashes = _load_hashes()
    if hashes.get(decisions_path) == content_hash:
        return 0
    hashes[decisions_path] = content_hash
    _save_hashes(hashes)

    # Append entry
    entry = f'''
## {time_str} — {os.path.basename(file_path)}

**File**: `{rel_path}`
**Trigger**: `{trigger_name}`
**Tool**: {tool_name}

### Diff

```diff
{diff}
```

### Current (excerpt)

```
{excerpt}
```

---

'''
    try:
        with open(decisions_path, 'a', encoding='utf-8') as f:
            f.write(entry)
    except Exception:
        return 0

    # Subtle notification
    print(f"💾 Design decision saved → decisions/{date_str}-design-{safe_slug}.md")
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception:
        # Never block user on hook errors
        sys.exit(0)
