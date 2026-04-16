#!/usr/bin/env python3
# DESIGN FOCUS REDIRECT — Nudge user toward /design-stack on design intent
# Alex Hale (2026-04-14)
# UserPromptSubmit hook
#
# On UserPromptSubmit, if prompt matches design-intent keywords and no
# design-stack invocation is active in recent history, emit a soft nudge
# suggesting /design-stack. Debounced to 15 min per session.

import hashlib
import json
import os
import re
import sys
import time

# Regex compiled at import time (cheap on repeated fires)
DESIGN_KEYWORDS = [
    re.compile(r'\bdesign(?:ing)?\b', re.I),
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

_cwd_hash = hashlib.md5(os.getcwd().encode()).hexdigest()[:8]
DEBOUNCE_FILE = os.path.expanduser(f'~/.claude/sensory-memory/design-focus-debounce-{_cwd_hash}')
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

    if not prompt or len(prompt) < 10:
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

    # Debounce check
    now = time.time()
    os.makedirs(os.path.dirname(DEBOUNCE_FILE), exist_ok=True)
    try:
        if os.path.exists(DEBOUNCE_FILE):
            last = float(open(DEBOUNCE_FILE).read().strip() or '0')
            if now - last < DEBOUNCE_SECS:
                return 0
    except Exception:
        pass

    # Update debounce file
    try:
        with open(DEBOUNCE_FILE, 'w') as f:
            f.write(str(now))
    except Exception:
        pass

    # Emit nudge to stderr (hook protocol — stderr feeds into next turn context)
    truncated = prompt[:60] + ('...' if len(prompt) > 60 else '')
    nudge = f"""
💡 Design intent detected. Consider: /design-stack "{truncated}" [--new|--refactor|--critique]
  • 9-phase pipeline (intent → refs → decisions → generate → verify → critique)
  • Auto-loads ua-ux defaults + ui-ux-pro-max options + frontend-design ethos
  • Composes Figma, shadcn MCP, Playwright, Opus vision in one flow

One-time nudge per 15min. Ignore if you prefer direct /ua-ux invocation.
"""
    print(nudge, file=sys.stderr)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception:
        # Never block user on hook errors
        sys.exit(0)
