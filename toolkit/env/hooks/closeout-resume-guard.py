#!/usr/bin/env python3
"""Stop hook: enforce that closeout-stack invocations end with a resume prompt.

Behavior:
  * Read the Stop hook JSON payload from stdin.
  * If closeout-stack was NOT invoked this session → exit 0 (no-op).
  * If closeout-stack WAS invoked AND the last assistant message contains a
    fenced code block matching the resume-prompt schema → exit 0.
  * Otherwise → exit 2 with a stderr message instructing Claude to emit one.
  * If stop_hook_active is true (loop guard) → exit 0 regardless.
  * On any parse error or missing file → exit 0. Never crash the harness.

Coverage scope:
  Layer 2 of the resume-prompt contract — clean Stop events ONLY. Crash, kill,
  network drop, and Ctrl+C scenarios that interrupt a session before clean
  termination cannot trigger this hook. Layer 1 (the SKILL.md Step 10
  EXTREMELY-IMPORTANT block) is the sole enforcement in those cases.

Performance:
  Uses a fast O(file-size) substring precheck before parsing JSONL. Sessions
  where closeout-stack was never invoked exit in <5ms. Full parse only runs
  when the precheck flags a potential invocation.

Detection rules:
  * Invocation: assistant Skill tool_use with input.skill in
    ("closeout-stack", "closeout"). Text mentions do not count — they would
    false-positive on every meta-discussion of the skill.
  * Resume prompt: a fenced code block whose first content line starts with
    "cd ~/" or "Resume " (allowing an optional "STATUS: partial" prefix line)
    AND contains "NEXT:" at the start of a later line. Matches the schema in
    ~/.claude/skills/closeout-stack/assets/resume-prompt.md.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Resume-prompt structural pattern — requires anchors, not arbitrary substrings.
#
#   Opening fence (any/no language tag).
#   Optional STATUS: partial header line.
#   Required first content line starts with `cd ~/` OR `Resume ` (line-anchored).
#   Lazy middle.
#   Required NEXT: line at line start (re.MULTILINE so ^ matches after \n).
#   Lazy middle, then closing fence.
RESUME_PROMPT_PATTERN = re.compile(
    r"```[^\n]*\n"
    r"(?:STATUS:[^\n]*\n)?"
    r"(?:cd\s+~/[^\n]+|Resume\s+[^\n]+)\n"
    r"[\s\S]*?"
    r"^NEXT:[^\n]+"
    r"[\s\S]*?```",
    re.MULTILINE,
)

# Fast precheck strings: if NONE appear in the raw transcript bytes, the skill
# was never invoked and we exit immediately without JSON parsing.
PRECHECK_NEEDLES = (b'"closeout-stack"', b'"closeout"')


def _extract_text(content) -> str:
    """Flatten Claude message content (string or list of blocks) to plain text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if not isinstance(block, dict):
                continue
            btype = block.get("type")
            if btype == "text":
                parts.append(block.get("text", ""))
            elif btype == "tool_use":
                name = block.get("name", "")
                inp = block.get("input", {})
                parts.append(f"[tool_use:{name} {json.dumps(inp, default=str)}]")
            elif btype == "tool_result":
                inner = block.get("content", "")
                parts.append(_extract_text(inner))
        return "\n".join(parts)
    return ""


def _iter_events(transcript_path: Path):
    try:
        with transcript_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue
    except OSError:
        return


def _precheck_skill_mentioned(path: Path) -> bool:
    """Cheap byte-level scan: does the transcript even mention the skill name?

    Returns False fast if not — saves a full JSONL parse on every Stop event
    in sessions where closeout-stack never came up. False positives here are
    fine; the full parser disambiguates.
    """
    try:
        with path.open("rb") as fh:
            blob = fh.read()
    except OSError:
        return False
    return any(needle in blob for needle in PRECHECK_NEEDLES)


def _last_closeout_invocation_index(events) -> int:
    """Return the index of the LAST assistant event containing a Skill tool_use
    for closeout-stack. Returns -1 if never invoked.

    Detection is structural (Skill tool_use only). Text mentions don't count —
    those false-positive on every meta-discussion of the skill.
    """
    last = -1
    for i, ev in enumerate(events):
        if ev.get("type") != "assistant":
            continue
        msg = ev.get("message") or {}
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") != "tool_use" or block.get("name") != "Skill":
                continue
            inp = block.get("input") or {}
            skill = (inp.get("skill") or "").lower()
            if skill in ("closeout-stack", "closeout"):
                last = i
                break
    return last


def _resume_prompt_emitted_after(events, start_idx: int) -> bool:
    """Did any assistant text block after `start_idx` contain a valid resume prompt?

    Walks forward from start_idx+1. Once a valid prompt is found, the closeout
    invocation is considered SATISFIED — future Stop events won't re-block.

    This semantic matters for two cases:
      * Race condition: the current Stop event fires before the assistant text
        is flushed to disk. We block once. The next Stop event (after Claude
        emits per the message) will find the prompt and pass.
      * Future turns: after a closeout produced a valid prompt, subsequent
        non-closeout work in the same session must not re-trigger blocking.
    """
    for i in range(start_idx + 1, len(events)):
        ev = events[i]
        if ev.get("type") != "assistant":
            continue
        msg = ev.get("message") or {}
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") != "text":
                continue
            if RESUME_PROMPT_PATTERN.search(block.get("text", "")):
                return True
    return False


def main() -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, ValueError):
        return 0

    if payload.get("stop_hook_active"):
        return 0

    transcript_path = payload.get("transcript_path")
    if not transcript_path:
        return 0
    path = Path(transcript_path)
    if not path.exists():
        return 0

    # Fast precheck — bail out if the skill name doesn't appear at all.
    if not _precheck_skill_mentioned(path):
        return 0

    events = list(_iter_events(path))
    if not events:
        return 0

    closeout_idx = _last_closeout_invocation_index(events)
    if closeout_idx < 0:
        return 0  # Never invoked

    if _resume_prompt_emitted_after(events, closeout_idx):
        return 0  # Satisfied — a valid prompt was emitted after the invocation

    sys.stderr.write(
        "closeout-stack was invoked this session but the final assistant message "
        "does not contain a resume prompt. Per the closeout-stack Step 10 contract, "
        "emit a fenced code block matching ~/.claude/skills/closeout-stack/assets/"
        "resume-prompt.md before ending the turn. The block's first content line "
        "must start with 'cd ~/' or 'Resume ' AND a later line must start with "
        "'NEXT:'.\n"
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
