#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
NC='\033[0m'
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Copy commit-gate.py
if [ -f "$HOME/.claude/hooks/commit-gate.py" ]; then
  if cmp -s "$SCRIPT_DIR/configs/commit-gate.py" "$HOME/.claude/hooks/commit-gate.py"; then
    echo -e "  ${GREEN}✓${NC} current commit-gate.py already installed"
  else
    echo "  Existing commit-gate.py differs from the bundled version; preserve it and review an update before replacement."
  fi
else
  cp "$SCRIPT_DIR/configs/commit-gate.py" "$HOME/.claude/hooks/commit-gate.py"
  chmod +x "$HOME/.claude/hooks/commit-gate.py"
  echo -e "  ${GREEN}✓${NC} Installed commit-gate.py"
fi

echo "  Commit gate file installed. Phase 5 checks its settings registration."
echo "  Existing settings are preserved; optional agents, CARL and other hooks require manual setup."
