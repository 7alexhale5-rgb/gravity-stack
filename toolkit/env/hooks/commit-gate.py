#!/usr/bin/env python3
"""
Claude Code commit-gate hook (PreToolUse on Bash).
Blocks git commits in TypeScript projects if tsc --noEmit fails.
Exit 0 = allow, Exit 2 = block.
"""
import json, sys, subprocess, os

try:
    raw = sys.stdin.read()
    if not raw.strip():
        sys.exit(0)
    data = json.loads(raw)
except (json.JSONDecodeError, ValueError, OSError):
    sys.exit(0)

cmd = data.get('tool_input', {}).get('command', '')

if 'git commit' not in cmd:
    sys.exit(0)

if not (os.path.exists('tsconfig.json') or os.path.exists('package.json')):
    sys.exit(0)

if os.path.exists('tsconfig.json'):
    result = subprocess.run(
        ['npx', 'tsc', '--noEmit'],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        # tsc writes errors to stdout; filter out .next/dev/types (stale route cache)
        errors = [l for l in result.stdout.splitlines() if 'error TS' in l and '.next/dev/types' not in l]
        if errors:
            print(f"COMMIT BLOCKED: {len(errors)} TypeScript error(s):\n" + "\n".join(errors[:10]), file=sys.stderr)
            sys.exit(2)
        # Only .next/dev/types errors — allow (they regenerate on next dev)

sys.exit(0)
