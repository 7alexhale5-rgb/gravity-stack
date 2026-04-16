#!/usr/bin/env python3
"""PostToolUse hook: log every closeout-stack Skill invocation to JSONL.

Fires on every Skill tool_use. If the invoked skill is closeout-stack (or its
"closeout" alias), appends one JSON line to ~/.claude/logs/closeout-runs.jsonl.
Silent otherwise.

Log entry fields: ts, session_id, cwd, skill, skill_args, transcript_path.
These enable Phase 3 monitoring: daily jq review of invocations, correlation
with Stop-hook outcomes (by session_id), and data-driven decisions on the
SessionEnd companion hook + close-day/pause-work coexistence.

Failure mode: exit 0 on any error. PostToolUse is advisory — the tool already
ran. Crashing this hook would add noise without signal.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path.home() / ".claude" / "logs"
LOG_FILE = LOG_DIR / "closeout-runs.jsonl"
TARGET_SKILLS = ("closeout-stack", "closeout")


def main() -> int:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return 0
        payload = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return 0

    if payload.get("tool_name") != "Skill":
        return 0

    tool_input = payload.get("tool_input") or {}
    skill = (tool_input.get("skill") or "").lower()
    if skill not in TARGET_SKILLS:
        return 0

    entry = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "session_id": payload.get("session_id", ""),
        "cwd": payload.get("cwd", ""),
        "skill": skill,
        "skill_args": tool_input.get("args", ""),
        "transcript_path": payload.get("transcript_path", ""),
    }

    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, default=str) + "\n")
    except OSError:
        pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
