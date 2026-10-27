#!/usr/bin/env python3
"""
TOKEN_BUDGET — Enhanced bracket display for CARL.
Adds actual token counts and threshold warnings to context brackets.
"""
from __future__ import annotations

MAX_CONTEXT = 1_000_000  # Default window; see context_window_for_model().

# Context window per model family. This is the one place the rule lives:
# carl-hook.py imports it instead of keeping its own copy, so the two can
# never drift apart. Never re-inline a window number into a caller.
#
# Why it matters: the bracket percentage is `100 - tokens*100//window`, so the
# window IS the denominator. Using 1M for a 200K model reports FRESH when only
# ~15% of the real window is left.
#
# First match wins, so narrower keys come first.
_CONTEXT_WINDOWS: tuple[tuple[str, int], ...] = (
    ("sonnet-4-5", 200_000),   # legacy 200K
    ("opus-4-5", 200_000),     # legacy 200K
    ("haiku-5", 1_000_000),    # Haiku 5.5: 1M window
    ("haiku", 200_000),        # Haiku 4.5 and older
    ("opus", 1_000_000),
    ("sonnet", 1_000_000),
    ("fable", 1_000_000),
    ("mythos", 1_000_000),
)

# Unrecognized model: assume the SMALL window. Being wrong small costs an early
# handoff nudge; being wrong large costs a silent overrun. Matching a family
# above keeps a future Opus/Sonnet release correct without an edit here.
UNKNOWN_MODEL_CONTEXT = 200_000


def context_window_for_model(model: str | None) -> int:
    """Context window in tokens for `model`. Conservative when unrecognized."""
    if not model:
        return UNKNOWN_MODEL_CONTEXT
    m = model.lower()
    for key, window in _CONTEXT_WINDOWS:
        if key in m:
            return window
    return UNKNOWN_MODEL_CONTEXT


def format_token_count(tokens: int) -> str:
    """Format token count for display: 920000 → '920K', 1000000 → '1.0M'."""
    if tokens <= 0:
        return "0"
    if tokens >= 1_000_000:
        return f"{tokens / 1_000_000:.1f}M"
    return f"{tokens // 1000}K"


def format_bracket(
    bracket: str, pct_remaining: float | None, window: int | None = None
) -> str:
    """Format bracket with actual token counts.

    `window` is the model's real context window; omit it only when the caller
    cannot determine the model. The total used to be hardcoded to "1M" here,
    which mislabelled every 200K session.
    """
    if pct_remaining is None:
        return f"[{bracket}] (context unknown)"

    win = window or MAX_CONTEXT
    tokens_remaining = int(win * pct_remaining / 100)
    tokens_str = format_token_count(tokens_remaining)
    total_str = format_token_count(win)
    return (
        f"[{bracket}] ({pct_remaining:.0f}% remaining · "
        f"~{tokens_str} of {total_str} tokens left)"
    )


def get_budget_warning(pct_remaining: float | None) -> str | None:
    """Return warning text if at a threshold, else None."""
    if pct_remaining is None:
        return None
    if pct_remaining <= 40:
        return "DEPLETED — use /plan (subagent isolation) for remaining work. Consider /handoff."
    if pct_remaining <= 60:
        return "Context over halfway — consider /sc or /handoff soon."
    return None
