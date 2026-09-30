#!/usr/bin/env python3
"""Claude PreToolUse hook: block commits when TypeScript checking cannot pass."""

import json
import os
from pathlib import Path
import shlex
import subprocess
import sys


def commit_directory(command, base):
    try:
        words = shlex.split(command)
    except ValueError:
        return None
    for index, word in enumerate(words):
        if word != "git":
            continue
        directory = base
        position = index + 1
        while position < len(words):
            flag = words[position]
            if flag in ("-C", "-c", "--git-dir", "--work-tree"):
                if position + 1 >= len(words):
                    return None
                if flag == "-C":
                    directory = (directory / words[position + 1]).resolve()
                position += 2
            elif flag.startswith("-C") and len(flag) > 2:
                directory = (directory / flag[2:]).resolve()
                position += 1
            elif flag.startswith(("-c", "--git-dir=", "--work-tree=")):
                position += 1
            else:
                break
        if position < len(words) and words[position] == "commit":
            return directory
    return None


try:
    payload = json.load(sys.stdin)
    tool = payload.get("tool_input", {})
    base = Path(payload.get("cwd") or tool.get("cwd") or os.getcwd()).resolve()
    directory = commit_directory(tool.get("command", ""), base)
except (ValueError, TypeError, OSError, AttributeError):
    sys.exit(0)

if directory is None or not (directory / "tsconfig.json").is_file():
    sys.exit(0)

try:
    check = subprocess.run(
        ["npx", "tsc", "--noEmit"],
        cwd=str(directory),
        capture_output=True,
        text=True,
        timeout=60,
    )
    if check.returncode != 0:
        detail = (check.stderr or check.stdout).strip()[:1000]
        print(
            "COMMIT BLOCKED: TypeScript check failed"
            + (":\n" + detail if detail else ""),
            file=sys.stderr,
        )
        sys.exit(2)
except (OSError, subprocess.TimeoutExpired, subprocess.SubprocessError) as error:
    print(
        f"COMMIT BLOCKED: TypeScript check unavailable ({type(error).__name__})",
        file=sys.stderr,
    )
    sys.exit(2)

sys.exit(0)
