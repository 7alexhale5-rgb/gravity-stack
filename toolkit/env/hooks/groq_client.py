#!/usr/bin/env python3
"""
Shared Groq API client for Gravity Stack hooks/scripts.
Single source of truth for API key loading and LLM calls.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path

DEFAULT_MODEL = "moonshotai/kimi-k2-instruct-0905"
DEFAULT_TIMEOUT = 15
API_URL = "https://api.groq.com/openai/v1/chat/completions"


def _load_api_key() -> str:
    """Load Groq API key from env or ~/.zshrc (no eval, direct parse)."""
    key = os.environ.get("GROQ_API_KEY", "")
    if key:
        return key

    zshrc = Path.home() / ".zshrc"
    if not zshrc.exists():
        return ""

    try:
        for line in zshrc.read_text().splitlines():
            stripped = line.strip()
            if stripped.startswith("export GROQ_API_KEY="):
                value = stripped.split("=", 1)[1].strip()
                # Remove surrounding quotes
                if (value.startswith('"') and value.endswith('"')) or (
                    value.startswith("'") and value.endswith("'")
                ):
                    value = value[1:-1]
                return value
    except Exception:
        pass
    return ""


def log_failure(reason: str, log_name: str = "groq-failures"):
    """Log API failures for visibility."""
    log_path = Path.home() / ".claude" / "sensory-memory" / f"{log_name}.log"
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a") as f:
            f.write(f"{datetime.now().isoformat()} | {reason}\n")
    except Exception:
        pass


def call_groq(
    prompt: str,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 1000,
    timeout: int = DEFAULT_TIMEOUT,
    json_mode: bool = True,
) -> dict | None:
    """Call Groq API. Returns parsed JSON dict or None on failure.

    Uses direct file parsing for API key (no eval/shell injection).
    Sends the key and prompt in the HTTPS request, never process arguments.
    Validates response structure before returning.
    """
    deadline = time.monotonic() + timeout
    api_key = _load_api_key()
    if not api_key:
        log_failure("no_api_key")
        return None

    payload: dict = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": max_tokens,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    try:
        # Config travels over stdin: neither credentials nor prompts enter argv.
        # Curl bounds slow-drip reads; the parent bounds connection and all reading.
        if "\r" in api_key or "\n" in api_key:
            log_failure("invalid_key_header")
            return None
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            log_failure("transport_timeout")
            return None
        config = "\n".join([
            "url = " + json.dumps(API_URL),
            "header = " + json.dumps("Authorization: Bearer " + api_key, ensure_ascii=False),
            'header = "Content-Type: application/json"',
            "data = " + json.dumps(json.dumps(payload), ensure_ascii=False),
        ])
        result = subprocess.run(
            ["curl", "--silent", "--show-error", "--fail", "--max-time",
             str(remaining), "--config", "-"],
            input=config, capture_output=True, text=True, timeout=remaining,
        )
        if result.returncode:
            log_failure("transport_exit_" + str(result.returncode))
            return None
        if time.monotonic() >= deadline:
            log_failure("transport_timeout")
            return None
        response = json.loads(result.stdout)

        # Validate response structure (OWASP A03 mitigation)
        if not isinstance(response, dict) or "choices" not in response:
            log_failure("invalid_response_structure")
            return None

        choices = response.get("choices", [])
        if not choices or not isinstance(choices[0], dict):
            log_failure("empty_choices")
            return None

        content = choices[0].get("message", {}).get("content", "")
        if not isinstance(content, str) or not content.strip():
            log_failure("empty_content")
            return None

        return json.loads(content)

    except json.JSONDecodeError:
        log_failure("json_decode_error")
        return None
    except subprocess.TimeoutExpired:
        log_failure("transport_timeout")
        return None
    except Exception as error:
        log_failure(f"unexpected_{type(error).__name__}")
        return None
