#!/usr/bin/env python3
"""
Shared Groq API client for Gravity Stack hooks/scripts.
Single source of truth for API key loading and LLM calls.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

DEFAULT_MODEL = "moonshotai/kimi-k2-instruct-0905"
DEFAULT_TIMEOUT = 15


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
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
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
    Uses curl subprocess with key via stdin-safe argument passing.
    Validates response structure before returning.
    """
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
        result = subprocess.run(
            ["curl", "-s", "--max-time", str(timeout),
             "https://api.groq.com/openai/v1/chat/completions",
             "-H", f"Authorization: Bearer {api_key}",
             "-H", "Content-Type: application/json",
             "-d", json.dumps(payload)],
            capture_output=True, text=True, timeout=timeout + 5,
        )

        if result.returncode != 0:
            log_failure(f"curl_exit_{result.returncode}")
            return None

        response = json.loads(result.stdout)

        # Validate response structure (OWASP A03 mitigation)
        if not isinstance(response, dict) or "choices" not in response:
            log_failure(f"invalid_response_structure: {result.stdout[:200]}")
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

    except json.JSONDecodeError as e:
        log_failure(f"json_decode_error: {e}")
        return None
    except subprocess.TimeoutExpired:
        log_failure("timeout")
        return None
    except Exception as e:
        log_failure(f"unexpected: {type(e).__name__}: {e}")
        return None
