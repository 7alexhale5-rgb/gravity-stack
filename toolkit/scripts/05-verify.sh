#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

PASS=0
FAIL=0

check() {
  if eval "$2" &>/dev/null; then
    echo -e "  ${GREEN}✓${NC} $1 $(eval "$3" 2>/dev/null || echo '')"
    PASS=$((PASS + 1))
  else
    echo -e "  ${RED}✗${NC} $1"
    FAIL=$((FAIL + 1))
  fi
}

echo -e "${BOLD}╔══════════════════════════════════════╗${NC}"
echo -e "${BOLD}║   GRAVITY STACK — VERIFICATION       ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════╝${NC}"
echo ""

commit_gate_registered() {
  python3 - <<'PYTHON'
import json, os
from pathlib import Path
try:
    settings = json.loads((Path.home() / '.claude/settings.json').read_text())
    gate = Path.home() / '.claude/hooks/commit-gate.py'
    commands = [hook.get('command', '') for group in settings.get('hooks', {}).get('PreToolUse', []) if group.get('matcher') == 'Bash' for hook in group.get('hooks', []) if hook.get('type') == 'command']
    registered = any(str(gate) in os.path.expanduser(os.path.expandvars(command)) for command in commands)
    raise SystemExit(0 if gate.is_file() and registered else 1)
except (OSError, ValueError, TypeError, AttributeError):
    raise SystemExit(1)
PYTHON
}

echo -e "${BOLD}Foundation:${NC}"
check "Homebrew" "command -v brew" "brew --version 2>/dev/null | head -1 | awk '{print \$2}'"
check "Node.js" "command -v node" "node --version"
check "Python" "command -v python3" "python3 --version 2>&1 | awk '{print \$2}'"
check "Docker" "command -v docker" "docker --version 2>/dev/null | awk '{print \$3}' | tr -d ','"
check "Git" "command -v git" "git --version 2>/dev/null | awk '{print \$3}'"
check "gh CLI" "command -v gh" "gh --version 2>/dev/null | head -1 | awk '{print \$3}'"
echo ""

echo -e "${BOLD}Claude Code:${NC}"
check "CLI installed" "command -v claude" "claude --version 2>/dev/null || echo 'installed'"
check "Settings found" "test -f $HOME/.claude/settings.json" "echo '~/.claude/settings.json'"
check "Hooks directory" "test -d $HOME/.claude/hooks" "echo '~/.claude/hooks/'"
check "Memory directory" "test -d $HOME/.claude/memory" "echo '~/.claude/memory/'"
echo ""

check "Commit gate file and registration" "commit_gate_registered" "echo 'read back from settings'"

TOTAL=$((PASS + FAIL))
echo -e "${BOLD}Results: ${GREEN}${PASS}/${TOTAL} passed${NC}"

if [ "$FAIL" -eq 0 ]; then
  echo -e "\n${GREEN}${BOLD}Status: FOUNDATION AND COMMIT REGISTRATION CHECKS PASSED${NC}"
else
  echo -e "\n${RED}${BOLD}Status: ${FAIL} CHECK(S) FAILED${NC}"
  echo "  Run individual phase scripts to fix issues."
  exit 1
fi

echo "Live hook firing, agent selection, optional CARL and MCP connections still need separate checks."
