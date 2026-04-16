#!/bin/bash
# Auto-Instinct Observer Trigger
# Fires on SessionStart, runs observer in background via nohup
# Non-blocking: exits immediately (<50ms), observer runs async

OBS_FILE="$HOME/.claude/homunculus/observations.jsonl"
OBSERVER_SPEC="$HOME/.claude/plugins/marketplaces/everything-claude-code/skills/continuous-learning-v2/agents/observer.md"
MIN_LINES=20

# Skip if no observations or too few
if [ ! -s "$OBS_FILE" ]; then
  exit 0
fi

LINE_COUNT=$(wc -l < "$OBS_FILE" 2>/dev/null | tr -d ' ')
if [ "$LINE_COUNT" -lt "$MIN_LINES" ]; then
  exit 0
fi

# Skip if observer spec doesn't exist
if [ ! -f "$OBSERVER_SPEC" ]; then
  exit 0
fi

# Fire background Haiku analysis (non-blocking)
nohup claude --print --model haiku "You are the ECC observer agent. Read the observer spec at $OBSERVER_SPEC and execute it against observations in $OBS_FILE. Create instincts in ~/.claude/homunculus/instincts/personal/. Archive processed observations. Be conservative — require 3+ occurrences for behavioral instincts." > /dev/null 2>&1 &

exit 0
