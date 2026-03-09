#!/usr/bin/env python3
"""
Commit Gate — Blocks git commits if TypeScript type checking fails.
Exit 0 = allow, Exit 2 = block.
"""
import json
import sys
import subprocess
import os

data = json.load(sys.stdin)
cmd = data.get("tool_input", {}).get("command", "")

if "git commit" not in cmd:
    sys.exit(0)

if not (os.path.exists("tsconfig.json") or os.path.exists("package.json")):
    sys.exit(0)

if os.path.exists("tsconfig.json"):
    result = subprocess.run(
        ["npx", "tsc", "--noEmit"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        print(f"COMMIT BLOCKED: TypeScript errors found:\n{result.stderr[:1000]}")
        sys.exit(2)

sys.exit(0)
