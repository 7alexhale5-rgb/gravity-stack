#!/usr/bin/env python3
"""
TOKEN_BUDGET — Enhanced bracket display for CARL.
Adds actual token counts and threshold warnings to context brackets.
"""
from __future__ import annotations

MAX_CONTEXT = 1_000_000  # Opus 4.6 1M context


def format_token_count(tokens: int) -> str:
    """Format token count for display: 920000 → '920K', 1000000 → '1.0M'."""
    if tokens <= 0:
        return "0"
    if tokens >= 1_000_000:
        return f"{tokens / 1_000_000:.1f}M"
    return f"{tokens // 1000}K"


def format_bracket(bracket: str, pct_remaining: float | None) -> str:
    """Format bracket with actual token counts."""
    if pct_remaining is None:
        return f"[{bracket}] (fresh session)"

    tokens_remaining = int(MAX_CONTEXT * pct_remaining / 100)
    tokens_str = format_token_count(tokens_remaining)
    return f"[{bracket}] ({pct_remaining:.0f}% remaining · ~{tokens_str} of 1M tokens left)"


def get_budget_warning(pct_remaining: float | None) -> str | None:
    """Return warning text if at a threshold, else None."""
    if pct_remaining is None:
        return None
    if pct_remaining <= 40:
        return "DEPLETED — use /plan (subagent isolation) for remaining work. Consider /handoff."
    if pct_remaining <= 60:
        return "Context over halfway — consider /sc or /handoff soon."
    return None
