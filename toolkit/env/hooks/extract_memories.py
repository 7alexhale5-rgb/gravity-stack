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
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Shared Groq client (Fix 3.1 + 3.2 from audit)
sys.path.insert(0, str(Path(__file__).parent))
from groq_client import call_groq, log_failure

# --- Configuration ---
MAX_SESSION_LINES = 80       # Read last N lines of session JSONL
MAX_PROMPT_MESSAGES = 30     # Include last N messages in extraction prompt
MIN_MESSAGES_SUBSTANTIAL = 4 # Minimum messages to consider extraction

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


def find_session_file(input_data: dict) -> Path | None:
    """Find the session JSONL file (same logic as carl-hook.py)."""
    session_id = input_data.get("sessionId", "") or input_data.get("session_id", "")
    cwd = input_data.get("cwd", "")

    if not session_id or not cwd:
        return None

    home = str(Path.home())
    search_path = Path(cwd)

    for _ in range(10):
        project_dir = str(search_path).replace("/", "-").lstrip("-")
        candidate = Path(home) / ".claude" / "projects" / f"-{project_dir}" / f"{session_id}.jsonl"
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
        project_dir = str(search_path).replace("/", "-").lstrip("-")
        candidate = Path(home) / ".claude" / "projects" / f"-{project_dir}" / "memory"
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
    extraction = call_groq(prompt)
    if not extraction:
        return  # Groq failed, silent fallback

    write_memories(extraction, memory_dir)
    # Output nothing — zero token cost to Claude


if __name__ == "__main__":
    main()
