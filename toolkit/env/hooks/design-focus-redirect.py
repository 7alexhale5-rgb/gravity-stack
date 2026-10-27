#!/usr/bin/env python3
# DESIGN FOCUS REDIRECT — Nudge user toward /design-stack on design intent
# Alex Hale (2026-04-14)
# UserPromptSubmit hook
#
# On UserPromptSubmit, if prompt matches design-intent keywords and no
# design-stack invocation is active in recent history, emit a soft nudge
# suggesting /design-stack. Debounced to 15 min per session.
# The nudge goes out as additionalContext JSON on stdout: UserPromptSubmit
# stderr on exit 0 never reaches the model.

import hashlib
import json
import os
import re
import sys
import time

# Regex compiled at import time (cheap on repeated fires)
DESIGN_KEYWORDS = [
    re.compile(r'\bdesign(?:ing)?\b', re.I),
    re.compile(r'\b(?:build|create|make)\s+(?:(?:me|us)\s+)?(?:(?:a|an|the)\s+)?(?:website|web\s+app|site)\b', re.I),
    re.compile(r'\bbuild (?:a |the )?(?:ui|page|screen|dashboard|modal|form|hero|landing|component)', re.I),
    re.compile(r'\bcreate (?:a |the )?(?:ui|page|screen|dashboard|modal|form|hero|landing|component)', re.I),
    re.compile(r'\bmake (?:a |the |it )?(?:look|feel|prettier|better|nicer)', re.I),
    re.compile(r'\bstyle (?:this|that|the)', re.I),
    re.compile(r'\b(?:make|fix) (?:the )?(?:layout|spacing|typography)', re.I),
    re.compile(r'\b(?:tailwind|shadcn|figma)\b', re.I),
    re.compile(r'\b(?:responsive|mobile view|dark mode)\b', re.I),
    re.compile(r'\b(?:component library|design system|style guide)\b', re.I),
    re.compile(r'\bcritique\b', re.I),
    re.compile(r'\b(?:ui|ux) (?:review|audit|polish)', re.I),
]

SKIP_IF_PRESENT = [
    re.compile(r'/design-stack\b'),
    re.compile(r'/planning-stack\b'),
    re.compile(r'/build-stack\b'),
    re.compile(r'/review-stack\b'),
    re.compile(r'/research-stack\b'),
    re.compile(r'/ua-ux\b'),
    re.compile(r'/ua-ux-critique\b'),
]

STATE_DIR = os.path.expanduser('~/.claude/sensory-memory')
DEBOUNCE_SECS = 15 * 60  # 15 minutes


def main() -> int:
    try:
        raw = sys.stdin.read()
        if not raw:
            return 0
        data = json.loads(raw)
        prompt = data.get('prompt', '')
    except Exception:
        return 0

    if not isinstance(prompt, str) or len(prompt) < 10:
        return 0
    # Harness notices are not user intent.
    if prompt.lstrip().startswith(('<task-notification', '[SYSTEM NOTIFICATION')):
        return 0

    prompt_stripped = prompt.strip()
    if prompt_stripped.startswith('/'):
        return 0

    # Skip if user is already in a related stack
    for pat in SKIP_IF_PRESENT:
        if pat.search(prompt):
            return 0

    # Check for design intent
    matched = False
    for pat in DESIGN_KEYWORDS:
        if pat.search(prompt):
            matched = True
            break
    if not matched:
        return 0

    # Debounce per session (falls back to cwd), so parallel sessions in one
    # folder do not silence each other.
    session = str(data.get('sessionId') or data.get('session_id') or data.get('cwd') or os.getcwd())
    key = hashlib.sha256(session.encode()).hexdigest()[:16]
    debounce_file = os.path.join(STATE_DIR, 'design-focus-debounce-' + key)
    now = time.time()
    os.makedirs(STATE_DIR, exist_ok=True)
    try:
        if os.path.exists(debounce_file):
            last = float(open(debounce_file).read().strip() or '0')
            if now - last < DEBOUNCE_SECS:
                return 0
    except Exception:
        pass

    # Update debounce file
    try:
        with open(debounce_file, 'w') as f:
            f.write(str(now))
    except Exception:
        pass

    truncated = prompt[:60] + ('...' if len(prompt) > 60 else '')
    nudge = f"""
💡 Design intent detected. Consider: /design-stack "{truncated}" [--new|--refactor|--critique]
  • 9-phase pipeline (intent → refs → decisions → generate → verify → critique)
  • Auto-loads ua-ux defaults + ui-ux-pro-max options + frontend-design ethos
  • Composes Figma, shadcn MCP, Playwright, Opus vision in one flow

One-time nudge per 15min. Ignore if you prefer direct /ua-ux invocation.
"""
    print(json.dumps({
        'hookSpecificOutput': {
            'hookEventName': 'UserPromptSubmit',
            'additionalContext': nudge.strip(),
        }
    }))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception:
        # Never block user on hook errors
        sys.exit(0)
