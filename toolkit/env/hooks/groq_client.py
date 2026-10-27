#!/usr/bin/env python3
"""
Shared Groq API client for Gravity Stack hooks/scripts.
Single source of truth for API key loading and LLM calls.
"""

from __future__ import annotations

import json
import os
import random
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Groq retires models without notice, and call_groq returns None on error, so a
# dead pin looks to every caller like "nothing to extract". The previous pin,
# moonshotai/kimi-k2-instruct-0905, now returns model_not_found, as does the
# whole llama chat family. Re-verify before re-pinning:
#   curl -s https://api.groq.com/openai/v1/models -H "Authorization: Bearer $GROQ_API_KEY"
# gpt-oss-* are reasoning models: they spend completion budget on reasoning
# before content, so call_groq sends reasoning_effort="low" for them (below).
DEFAULT_MODEL = "openai/gpt-oss-20b"
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
    """Log API failures for visibility.

    Each line names its caller, because several scripts share this client and a
    failure line that cannot say whose it is gets misread. `caller=` is appended,
    never prepended, so readers that split on the first " | " keep working.
    """
    caller = Path(sys.argv[0]).stem if sys.argv and sys.argv[0] else "unknown"
    log_path = Path.home() / ".claude" / "sensory-memory" / f"{log_name}.log"
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a") as f:
            f.write(f"{datetime.now().isoformat()} | {reason} | caller={caller}\n")
    except Exception:
        pass


# Failure kinds worth retrying: transient by nature. Everything else (bad key,
# retired model, malformed output) must keep failing loudly on attempt 1;
# retrying a permanent error only delays the log line that surfaces it.
# curl exits: 6/7 DNS+connect, 28 timeout, 35 SSL connect, 52 empty reply, 56 recv.
_RETRYABLE_CURL_EXITS = {6, 7, 28, 35, 52, 56}
_RETRYABLE_MARKERS = ("rate_limit", "429", "server_error", "service_unavailable",
                      "overloaded", "internal", "timeout")


def _is_retryable(kind: str) -> bool:
    kind = kind.lower()
    if kind.startswith("transport_exit_"):
        try:
            return int(kind.rsplit("_", 1)[1]) in _RETRYABLE_CURL_EXITS
        except ValueError:
            return False
    # Permanent whatever code it arrives under. Checked BEFORE the retryable
    # markers, because "rate_limit_exceeded_request_too_large" contains
    # "rate_limit". An oversized request is fixed by chunking, never by waiting.
    if "too_large" in kind:
        return False
    if kind.startswith(("no_api_key", "model_not_found", "invalid", "empty_",
                        "json_decode_error", "unexpected")):
        return False
    return any(m in kind for m in _RETRYABLE_MARKERS)


def call_groq(
    prompt: str,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 1000,
    timeout: int = DEFAULT_TIMEOUT,
    json_mode: bool = True,
    max_attempts: int = 3,
    deadline: float | None = None,
) -> dict | None:
    """Call Groq API with bounded retry. Returns parsed JSON dict or None.

    `timeout` bounds each attempt. `deadline` is a time.monotonic() timestamp
    for the whole call; without one the call makes a single attempt, so
    `timeout` stays the overall bound. With one, transient failures (per
    _is_retryable) retry up to max_attempts with ~2s/~6s jittered backoff, and a
    retry is skipped when backoff plus another full attempt would overshoot it.
    """
    if deadline is None:
        max_attempts = 1
    attempt = 0
    while True:
        attempt += 1
        result, kind = _call_groq_once(prompt, model, max_tokens, timeout, json_mode)
        if result is not None:
            return result
        if attempt >= max_attempts or not _is_retryable(kind):
            if attempt > 1:
                log_failure(f"gave_up_after_{attempt}_attempts: {kind}")
            return None
        backoff = (2.0 * (3 ** (attempt - 1))) * (0.75 + random.random() * 0.5)
        if time.monotonic() + backoff + timeout > deadline:
            log_failure(f"budget_exhausted_after_{attempt}_attempts: {kind}")
            return None
        log_failure(f"retry_{attempt} after {kind}")
        time.sleep(backoff)


def _call_groq_once(
    prompt: str,
    model: str,
    max_tokens: int,
    timeout: float,
    json_mode: bool,
) -> tuple[dict | None, str]:
    """Single Groq API call. Returns (parsed JSON dict, "") or (None, failure_kind).

    Uses direct file parsing for API key (no eval/shell injection).
    Sends the key and prompt in the HTTPS request, never process arguments.
    Validates response structure before returning.
    """
    deadline = time.monotonic() + timeout
    api_key = _load_api_key()
    if not api_key:
        log_failure("no_api_key")
        return None, "no_api_key"

    payload: dict = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": max_tokens,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    # gpt-oss-* spend completion budget on reasoning before content. Left
    # unconstrained, a tight max_tokens yields empty content, which every caller
    # reads as "nothing to extract".
    if model.startswith("openai/gpt-oss"):
        payload["reasoning_effort"] = "low"

    try:
        # Config travels over stdin: neither credentials nor prompts enter argv.
        # Curl bounds slow-drip reads; the parent bounds connection and all reading.
        if "\r" in api_key or "\n" in api_key:
            log_failure("invalid_key_header")
            return None, "invalid_key_header"
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            log_failure("transport_timeout")
            return None, "transport_timeout"
        config = "\n".join([
            "url = " + json.dumps(API_URL),
            "header = " + json.dumps("Authorization: Bearer " + api_key, ensure_ascii=False),
            'header = "Content-Type: application/json"',
            "data = " + json.dumps(json.dumps(payload), ensure_ascii=False),
        ])
        result = subprocess.run(
            # No --fail: an HTTP error body names its cause (rate limit vs
            # retired model vs bad key), which decides whether a retry can help.
            ["curl", "--silent", "--show-error", "--max-time",
             str(remaining), "--config", "-"],
            input=config, capture_output=True, text=True, timeout=remaining,
        )
        if result.returncode:
            log_failure("transport_exit_" + str(result.returncode))
            return None, "transport_exit_" + str(result.returncode)
        if time.monotonic() >= deadline:
            log_failure("transport_timeout")
            return None, "transport_timeout"
        response = json.loads(result.stdout)

        # Validate response structure (OWASP A03 mitigation)
        if not isinstance(response, dict) or "choices" not in response:
            # Name the actual failure class (code/type only, never the body), so
            # a rate limit, a retired model and a bad key are distinguishable.
            err = response.get("error") if isinstance(response, dict) else None
            if isinstance(err, dict):
                kind = str(err.get("code") or err.get("type") or "api_error")
                kind = "".join(c if c.isalnum() or c in "_-" else "_" for c in kind)[:64]
                # Groq reports "Request too large" under rate_limit_exceeded, but an
                # oversized request is permanent; carry that through to _is_retryable.
                if "too large" in str(err.get("message", "")).lower():
                    kind += "_request_too_large"
                log_failure(kind)
                return None, kind
            log_failure("invalid_response_structure")
            return None, "invalid_response_structure"

        choices = response.get("choices", [])
        if not choices or not isinstance(choices[0], dict):
            log_failure("empty_choices")
            return None, "empty_choices"

        content = choices[0].get("message", {}).get("content", "")
        if not isinstance(content, str) or not content.strip():
            log_failure("empty_content")
            return None, "empty_content"

        return json.loads(content), ""

    except json.JSONDecodeError:
        log_failure("json_decode_error")
        return None, "json_decode_error"
    except subprocess.TimeoutExpired:
        log_failure("transport_timeout")
        return None, "transport_timeout"
    except Exception as error:
        log_failure(f"unexpected_{type(error).__name__}")
        return None, f"unexpected_{type(error).__name__}"
