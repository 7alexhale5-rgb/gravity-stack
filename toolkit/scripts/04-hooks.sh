#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
NC='\033[0m'
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_ROOT="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
mkdir -p "$CONFIG_ROOT/hooks"

# Copy commit-gate.py
if [ -f "$CONFIG_ROOT/hooks/commit-gate.py" ]; then
  if cmp -s "$SCRIPT_DIR/configs/commit-gate.py" "$CONFIG_ROOT/hooks/commit-gate.py"; then
    echo -e "  ${GREEN}✓${NC} current commit-gate.py already installed"
  else
    echo "  Existing commit-gate.py differs from the bundled version; preserve it and review an update before replacement."
  fi
else
  cp "$SCRIPT_DIR/configs/commit-gate.py" "$CONFIG_ROOT/hooks/commit-gate.py"
  chmod +x "$CONFIG_ROOT/hooks/commit-gate.py"
  echo -e "  ${GREEN}✓${NC} Installed commit-gate.py"
fi

echo "  Commit gate file installed. Phase 5 checks its settings registration."
echo "  Existing settings are preserved; optional agents, CARL and other hooks require manual setup."
