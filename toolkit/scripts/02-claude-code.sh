#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
NC='\033[0m'

# Claude Code CLI
if command -v claude &>/dev/null; then
  echo -e "  ${GREEN}✓${NC} Claude Code already installed: $(claude --version 2>/dev/null || echo 'installed')"
else
  echo "  Installing Claude Code CLI..."
  npm install -g @anthropic-ai/claude-code
fi

# Directory structure
for dir in hooks memory backups; do
  if [ -d "$HOME/.claude/$dir" ]; then
    echo -e "  ${GREEN}✓${NC} ~/.claude/$dir/ exists"
  else
    mkdir -p "$HOME/.claude/$dir"
    echo -e "  ${GREEN}✓${NC} Created ~/.claude/$dir/"
  fi
done

# Copy template settings if no settings exist
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ ! -f "$HOME/.claude/settings.json" ]; then
  echo "  Copying template settings.json..."
  cp "$SCRIPT_DIR/configs/settings.json" "$HOME/.claude/settings.json"
  echo -e "  ${GREEN}✓${NC} Settings configured"
else
  echo -e "  ${GREEN}✓${NC} Settings already exist (not overwriting)"
fi
