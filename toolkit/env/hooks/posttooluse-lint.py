#!/usr/bin/env python3
"""PostToolUse Edit|Write hook: passive lint check for edited file.

Only runs when project root has the relevant config (tsconfig.json for tsc,
.eslintrc* / eslint.config.* for eslint). Silently skips otherwise.

Optimizations vs the inline version it replaces:
- Guards: no tsc/eslint invocation in projects without config (huge latency win)
- `npx --no-install`: fail fast if tools not locally installed (no auto-install)
- Lower timeout: 15s instead of 30s
- Runs from project root (not file dir) so tsc/eslint pick up the right config
- Graceful: silently skips on any error
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

LINTABLE_EXTS = {'.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs'}
TS_EXTS = {'.ts', '.tsx'}
ESLINT_CONFIG_FILES = [
    '.eslintrc', '.eslintrc.js', '.eslintrc.cjs', '.eslintrc.json',
    '.eslintrc.yml', '.eslintrc.yaml', 'eslint.config.js', 'eslint.config.mjs',
    'eslint.config.cjs', 'eslint.config.ts',
]
MAX_OUTPUT_CHARS = 500
SUBPROCESS_TIMEOUT = 15  # seconds


def find_project_root(file_path: str) -> Path | None:
    """Walk up from file's parent looking for tsconfig.json or package.json."""
    try:
        p = Path(file_path).resolve().parent
    except (OSError, ValueError):
        return None

    for _ in range(15):  # max 15 levels up — defensive bound
        if (p / 'tsconfig.json').exists() or (p / 'package.json').exists():
            return p
        if p.parent == p:  # reached filesystem root
            return None
        p = p.parent
    return None


def has_eslint_config(project_root: Path) -> bool:
    return any((project_root / f).exists() for f in ESLINT_CONFIG_FILES)


def run_check(cmd: list[str], cwd: Path) -> str:
    """Run a check command, return its output (stderr for tsc, stdout for eslint).
    Returns empty string on any failure (timeout, missing tool, exit-code-only).
    """
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT,
            cwd=str(cwd),
        )
        # tsc emits errors to stderr, eslint to stdout — return whichever is non-empty
        out = (r.stderr or r.stdout or '').strip()
        return out[:MAX_OUTPUT_CHARS]
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return ''


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    path = data.get('tool_input', {}).get('file_path', '')
    if not path:
        sys.exit(0)

    ext = os.path.splitext(path)[1].lower()
    if ext not in LINTABLE_EXTS:
        sys.exit(0)

    project_root = find_project_root(path)
    if project_root is None:
        sys.exit(0)

    results: list[str] = []

    # Run tsc only for TS files in projects with tsconfig.json
    if ext in TS_EXTS and (project_root / 'tsconfig.json').exists():
        out = run_check(['npx', '--no-install', 'tsc', '--noEmit'], project_root)
        if out:
            results.append(f"[tsc]\n{out}")

    # Run eslint only if project has an eslint config
    if has_eslint_config(project_root):
        out = run_check(['npx', '--no-install', 'eslint', path], project_root)
        if out:
            results.append(f"[eslint]\n{out}")

    output = '\n\n'.join(results)
    if output:
        print(output)


if __name__ == '__main__':
    main()
