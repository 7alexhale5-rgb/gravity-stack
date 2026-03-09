#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
NC='\033[0m'
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Copy commit-gate.py
if [ -f "$HOME/.claude/hooks/commit-gate.py" ]; then
  echo -e "  ${GREEN}✓${NC} commit-gate.py already installed"
else
  cp "$SCRIPT_DIR/configs/commit-gate.py" "$HOME/.claude/hooks/commit-gate.py"
  chmod +x "$HOME/.claude/hooks/commit-gate.py"
  echo -e "  ${GREEN}✓${NC} Installed commit-gate.py"
fi

echo -e "  ${GREEN}✓${NC} Hooks configured in settings.json"
echo "  Hook events: Notification, PreCompact, PreToolUse (x2), PostToolUse, SessionStart, UserPromptSubmit"
