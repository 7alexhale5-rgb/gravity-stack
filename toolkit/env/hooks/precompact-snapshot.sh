#!/usr/bin/env bash
# precompact-snapshot.sh — Auto-snapshot session state before context compaction.
#
# Fires from PreCompact hook in ~/.claude/settings.json. Two responsibilities:
#   1. Backup the raw session jsonl to ~/.claude/backups/ for recovery
#   2. Write a human-readable session-compact summary to ~/vault/sessions/
#
# Replaces a 600+ char inline shell heredoc that lived in settings.json. The
# inline version was a maintenance trap (escaping nightmare, hard to debug).
# Behavior is identical — just lives in a real file now.
#
# Created: 2026-04-08 (CC environment audit Wave 1, item 5)

set -uo pipefail
# Note: NOT using `set -e` — every step is best-effort, we never want to
# block compaction even if some part of the snapshot fails.

# 1. Backup the raw session jsonl
mkdir -p ~/.claude/backups
if [ -f ~/.claude/current-session.jsonl ]; then
    cp ~/.claude/current-session.jsonl \
       ~/.claude/backups/session-$(date +%Y%m%d-%H%M%S).jsonl 2>/dev/null || true
fi

# 2. Gather context for the human-readable summary
PROJECT=$(basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)")
GIT_STATUS=$(git status --short 2>/dev/null | head -20)
RECENT_FILES=$(git diff --name-only HEAD~3 2>/dev/null | head -15 || echo 'no recent commits')
DATE=$(date +%Y-%m-%d)
TIME=$(date +%H:%M)
SLUG=$(echo "$PROJECT" | tr ' ' '-' | tr '[:upper:]' '[:lower:]')

# 3. Write the session-compact summary
mkdir -p ~/vault/sessions
cat > ~/vault/sessions/${DATE}-compact-${SLUG}.md <<MVEOF
---
date: ${DATE}
type: session
project: ${PROJECT}
tags: [memory, session, ${PROJECT}, compact]
---

# Session Compact — ${DATE} — ${PROJECT}

Compacted at ${TIME}.

## Git Status
${GIT_STATUS:-No changes}

## Recent Files
${RECENT_FILES}
MVEOF

exit 0
