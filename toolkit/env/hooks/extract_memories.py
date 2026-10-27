#!/usr/bin/env python3
"""
EXTRACT_MEMORIES — PreCompact hook for Gravity Stack v4.
Reads session JSONL, extracts reusable knowledge via Groq API,
writes to T1 memory topic files.

Hook type: PreCompact (fires before context compaction)
Token cost: 0 (no output to Claude)
External cost: ~$0 (Groq free tier)
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

# Shared Groq client (Fix 3.1 + 3.2 from audit)
sys.path.insert(0, str(Path(__file__).parent))
from groq_client import _is_retryable, call_groq_detailed, log_failure

# --- Configuration ---
MAX_SESSION_LINES = 80       # Read last N lines of session JSONL
MAX_PROMPT_MESSAGES = 30     # Include last N messages in extraction prompt
MIN_MESSAGES_SUBSTANTIAL = 4 # Minimum messages to consider extraction

# Groq caps tokens per model, so a dedicated pin keeps this job from competing
# with other Groq callers for the same bucket. Override with EXTRACT_GROQ_MODEL.
EXTRACT_MODEL = os.environ.get("EXTRACT_GROQ_MODEL", "openai/gpt-oss-20b")

# --- Budget (the PreCompact hook timeout in settings.template.json is 20s) ---
# Retry must never push the hook past its timeout: a killed PreCompact is worse
# than a dropped extraction. Every Groq attempt is cut off at a 17s deadline
# the client enforces on curl itself. The current session goes first; a backlog
# replay starts only when a full call (6s + ~2.5s backoff + 6s) still fits.
HOOK_BUDGET_S = 20
BUDGET_RESERVE_S = 3         # writes + interpreter teardown
CALL_TIMEOUT_S = 6
MAX_ATTEMPTS = 2
FULL_CALL_S = MAX_ATTEMPTS * CALL_TIMEOUT_S + 2.5  # worst case incl. max backoff

# --- Dead letter (nothing is lost when Groq is down) ---
DEAD_LETTER_DIR = Path.home() / ".claude" / "sensory-memory" / "dead-letter"
DEAD_LETTER_CAP = 50         # newest kept; overflow is logged, never silent
DEAD_LETTER_MAX_AGE_DAYS = 30

# Correction signal words — if any appear, session is substantial regardless of length
CORRECTION_SIGNALS = [
    "no,", "don't", "stop", "not that", "actually,", "instead",
    "remember to", "always", "never", "from now on", "wrong",
]


def parse_session_messages(session_file: Path, max_lines: int = MAX_SESSION_LINES) -> list[dict]:
    """Parse session JSONL into simplified message list."""
    messages = []
    try:
        result = subprocess.run(
            ["tail", f"-{max_lines}", str(session_file)],
            capture_output=True, text=True, timeout=5,
        )
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            msg_type = data.get("type")
            message = data.get("message", {})
            role = message.get("role")

            if msg_type == "user" and role == "user":
                content = message.get("content", "")
                if isinstance(content, str) and content.strip():
                    messages.append({"role": "user", "content": content.strip()})

            elif msg_type == "assistant" and role == "assistant":
                content_blocks = message.get("content", [])
                if isinstance(content_blocks, list):
                    text_parts = [
                        block.get("text", "")
                        for block in content_blocks
                        if isinstance(block, dict) and block.get("type") == "text"
                    ]
                    combined = " ".join(t.strip() for t in text_parts if t.strip())
                    if combined:
                        messages.append({"role": "assistant", "content": combined})
    except Exception:
        pass
    return messages


def is_substantial_session(messages: list[dict]) -> bool:
    """Check if session has enough substance to warrant extraction."""
    if len(messages) >= MIN_MESSAGES_SUBSTANTIAL:
        return True
    # Check for correction signals in user messages
    user_text = " ".join(
        m["content"].lower() for m in messages if m["role"] == "user"
    )
    return any(signal in user_text for signal in CORRECTION_SIGNALS)


def build_extraction_prompt(messages: list[dict]) -> str:
    """Build the Groq extraction prompt from conversation messages."""
    # Truncate to last N messages
    recent = messages[-MAX_PROMPT_MESSAGES:]

    conversation_text = "\n".join(
        f"{'USER' if m['role'] == 'user' else 'ASSISTANT'}: {m['content'][:500]}"
        for m in recent
    )

    return f"""Analyze this conversation and extract ONLY genuinely novel, reusable knowledge.

Categories to extract (return empty arrays if nothing fits):
1. **feedback** — User corrections, preferences, "always do X", "never do Y", workflow rules
2. **decisions** — Architectural or implementation decisions made (not task-specific choices)
3. **problems_solutions** — Bugs encountered and their fixes, with enough detail to reuse

Return ONLY valid JSON. No preamble, no explanation:
{{"feedback": ["..."], "decisions": ["..."], "problems_solutions": [{{"problem": "...", "solution": "..."}}]}}

Skip: ephemeral task details, file names, specific code snippets, anything already obvious from the codebase.

CONVERSATION:
{conversation_text}"""


def _is_duplicate(content: str, memory_dir: Path, threshold: float = 0.70) -> bool:
    """Check if content already exists in memory files (dedup at write time)."""
    content_lower = content.lower()[:200]  # Compare first 200 chars
    for f in memory_dir.glob("*.md"):
        if f.name == "MEMORY.md":
            continue
        try:
            existing = f.read_text().lower()
            # Quick substring check before expensive comparison
            key_phrases = [w for w in content_lower.split() if len(w) > 5][:5]
            matches = sum(1 for phrase in key_phrases if phrase in existing)
            if key_phrases and matches / len(key_phrases) >= threshold:
                return True
        except Exception:
            continue
    return False


def write_memories(extraction: dict, memory_dir: Path) -> list[Path]:
    """Write extracted memories to T1 topic files. Returns list of files written."""
    files_written = []
    date_str = datetime.now().strftime("%Y%m%d-%H%M")
    items = []

    for fb in extraction.get("feedback", []):
        if fb and fb.strip():
            items.append(("feedback", fb.strip()))

    for dec in extraction.get("decisions", []):
        if dec and dec.strip():
            items.append(("decision", dec.strip()))

    for ps in extraction.get("problems_solutions", []):
        if isinstance(ps, dict) and ps.get("problem") and ps.get("solution"):
            items.append(("problem-solution", f"**Problem:** {ps['problem']}\n**Solution:** {ps['solution']}"))

    if not items:
        return files_written

    # Dedup: skip if all items already exist in memory (DA finding #2)
    novel_items = [(cat, content) for cat, content in items if not _is_duplicate(content, memory_dir)]
    if not novel_items:
        return files_written
    items = novel_items

    # Write all items to a single file per extraction run
    slug = re.sub(r"[^a-z0-9]+", "-", items[0][1][:40].lower()).strip("-")
    filename = f"auto-extract-{date_str}-{slug}.md"
    filepath = memory_dir / filename

    lines = [
        "---",
        f"name: auto-extract-{date_str}",
        f"description: Auto-extracted memories from session {date_str}",
        "type: auto-extract",
        "---",
        "",
    ]

    for category, content in items:
        lines.append(f"## [{category}]")
        lines.append(content)
        lines.append("")

    filepath.write_text("\n".join(lines))
    files_written.append(filepath)
    return files_written


def _atomic_write_json(path: Path, data: dict) -> None:
    """Write JSON so a reader never sees a half-written file."""
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def _project_dir_name(path) -> str:
    """Claude Code's transcript folder name for a working folder: every character
    that is not a letter or digit becomes '-'. Same rule as carl-hook.py's
    _project_dir_name (a test keeps the two identical)."""
    return re.sub(r"[^A-Za-z0-9]", "-", str(path))


def _extract_and_write(prompt: str, memory_dir: Path, deadline: float) -> str:
    """One extraction (with the client's internal retry). Returns "" when memories
    were processed, else the failure kind; _is_retryable(kind) says whether the
    chunk is worth keeping for a later replay."""
    extraction, kind = call_groq_detailed(
        prompt, model=EXTRACT_MODEL, timeout=CALL_TIMEOUT_S,
        max_attempts=MAX_ATTEMPTS, deadline=deadline
    )
    if extraction is None:
        return kind or "unexpected_none"
    if extraction:  # an empty object means nothing worth saving
        write_memories(extraction, memory_dir)
    return ""


def _dead_letter_park(prompt: str, memory_dir: Path, reason: str) -> None:
    """Park an unprocessed chunk for replay. A delayed extraction is recoverable;
    returning on a Groq failure lost it outright with no trace."""
    try:
        DEAD_LETTER_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
        _atomic_write_json(
            DEAD_LETTER_DIR / f"{stamp}.json",
            {"prompt": prompt, "memory_dir": str(memory_dir),
             "reason": reason, "parked_at": datetime.now().isoformat()},
        )
        log_failure(f"dead_letter_parked: {reason}")
    except Exception as exc:
        log_failure(f"dead_letter_park_failed: {type(exc).__name__}")


def _dead_letter_maintain() -> None:
    """Age-out and cap. Every discard is logged: a known loss, never a silent one."""
    if not DEAD_LETTER_DIR.is_dir():
        return
    try:
        files = sorted(DEAD_LETTER_DIR.glob("*.json"))
        cutoff = time.time() - DEAD_LETTER_MAX_AGE_DAYS * 86400
        for f in files:
            if f.stat().st_mtime < cutoff:
                log_failure(f"dead_letter_aged_out (>{DEAD_LETTER_MAX_AGE_DAYS}d): {f.name}")
                f.unlink(missing_ok=True)
        files = sorted(DEAD_LETTER_DIR.glob("*.json"))
        for f in files[:-DEAD_LETTER_CAP] if len(files) > DEAD_LETTER_CAP else []:
            log_failure(f"dead_letter_over_cap (>{DEAD_LETTER_CAP}), dropped oldest: {f.name}")
            f.unlink(missing_ok=True)
    except Exception as exc:
        log_failure(f"dead_letter_maintain_failed: {type(exc).__name__}")


def _dead_letter_recover_stale_claims() -> None:
    """Return claims left by a hook that was killed mid-replay. A claim older than
    the hook timeout cannot belong to a live run, so it goes back in the queue."""
    if not DEAD_LETTER_DIR.is_dir():
        return
    cutoff = time.time() - HOOK_BUDGET_S
    for claimed in DEAD_LETTER_DIR.glob("*.claiming-*"):
        try:
            if claimed.stat().st_mtime < cutoff:
                os.replace(claimed, claimed.with_name(claimed.name.split(".claiming-")[0] + ".json"))
                log_failure(f"dead_letter_claim_recovered: {claimed.name}")
        except OSError:
            continue


def _dead_letter_drain(deadline: float) -> None:
    """Replay parked chunks oldest-first, bounded by the hook's budget.

    Runs after the current session's extraction, so the backlog never starves
    fresh content. Each replay starts only when a full call still fits before
    the deadline. Claims each file by atomic rename so two concurrent sessions
    cannot process the same chunk.
    """
    if not DEAD_LETTER_DIR.is_dir():
        return
    for path in sorted(DEAD_LETTER_DIR.glob("*.json")):
        if deadline - time.monotonic() < FULL_CALL_S:
            return  # out of budget; the rest stay parked for the next run
        claimed = path.with_suffix(f".claiming-{os.getpid()}")
        try:
            os.replace(path, claimed)  # atomic claim; loser gets FileNotFoundError
        except OSError:
            continue
        try:
            payload = json.loads(claimed.read_text())
            memory_dir = Path(payload["memory_dir"])
            if not memory_dir.is_dir():
                log_failure(f"dead_letter_discarded_missing_dir: {path.name}")
                claimed.unlink(missing_ok=True)
                continue
            kind = _extract_and_write(payload["prompt"], memory_dir, deadline)
            if not kind:
                claimed.unlink(missing_ok=True)
                log_failure(f"dead_letter_replayed: {path.name}")
            elif not _is_retryable(kind):
                claimed.unlink(missing_ok=True)  # replaying cannot fix it
                log_failure(f"dead_letter_dropped_permanent: {kind}: {path.name}")
            else:
                os.replace(claimed, path)  # transient: requeue untouched
                return  # Groq is down; stop hammering it this run
        except Exception as exc:
            log_failure(f"dead_letter_replay_error: {type(exc).__name__}")
            try:
                os.replace(claimed, path)
            except OSError:
                pass
            return


def find_session_file(input_data: dict) -> Path | None:
    """Find the session JSONL file (same logic as carl-hook.py)."""
    session_id = input_data.get("sessionId", "") or input_data.get("session_id", "")
    cwd = input_data.get("cwd", "")

    # The hook input names the transcript directly; prefer it over the rebuilt path.
    given = input_data.get("transcript_path")
    if given and Path(given).is_file():
        return Path(given)

    if not session_id or not cwd:
        return None

    home = str(Path.home())
    search_path = Path(cwd)

    for _ in range(10):
        project_dir = _project_dir_name(search_path)
        candidate = Path(home) / ".claude" / "projects" / project_dir / f"{session_id}.jsonl"
        if candidate.exists():
            return candidate
        if search_path.parent == search_path:
            break
        search_path = search_path.parent
    return None


def find_memory_dir(cwd: str) -> Path | None:
    """Find the T1 memory directory for the current project."""
    home = str(Path.home())
    search_path = Path(cwd)

    for _ in range(10):
        project_dir = _project_dir_name(search_path)
        candidate = Path(home) / ".claude" / "projects" / project_dir / "memory"
        if candidate.exists():
            return candidate
        if search_path.parent == search_path:
            break
        search_path = search_path.parent
    return None


def main():
    """Main hook entry point. Reads from stdin, outputs nothing."""
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        input_data = {}

    if not isinstance(input_data, dict):
        input_data = {}

    deadline = time.monotonic() + (HOOK_BUDGET_S - BUDGET_RESERVE_S)
    _dead_letter_recover_stale_claims()

    # Current session first, then the backlog with whatever budget is left, so a
    # short session still clears chunks parked during an earlier outage.
    _extract_current_session(input_data, deadline)
    _dead_letter_maintain()
    _dead_letter_drain(deadline)
    # Output nothing — zero token cost to Claude


def _extract_current_session(input_data: dict, deadline: float) -> None:
    session_file = find_session_file(input_data)
    if not session_file:
        return  # Silent exit

    messages = parse_session_messages(session_file)
    if not is_substantial_session(messages):
        return  # Session too short, skip

    cwd = input_data.get("cwd", str(Path.home()))
    memory_dir = find_memory_dir(cwd)
    if not memory_dir:
        return  # No memory dir found

    prompt = build_extraction_prompt(messages)
    kind = _extract_and_write(prompt, memory_dir, deadline)
    if kind and _is_retryable(kind):
        _dead_letter_park(prompt, memory_dir, kind)
    elif kind:
        log_failure(f"extraction_dropped_permanent: {kind}")


if __name__ == "__main__":
    main()
