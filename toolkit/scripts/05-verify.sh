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
    ((PASS++))
  else
    echo -e "  ${RED}✗${NC} $1"
    ((FAIL++))
  fi
}

echo -e "${BOLD}╔══════════════════════════════════════╗${NC}"
echo -e "${BOLD}║   GRAVITY STACK — VERIFICATION       ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════╝${NC}"
echo ""

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

TOTAL=$((PASS + FAIL))
echo -e "${BOLD}Results: ${GREEN}${PASS}/${TOTAL} passed${NC}"

if [ "$FAIL" -eq 0 ]; then
  echo -e "\n${GREEN}${BOLD}Status: ALL CHECKS PASSED ✓${NC}"
else
  echo -e "\n${RED}${BOLD}Status: ${FAIL} CHECK(S) FAILED${NC}"
  echo "  Run individual phase scripts to fix issues."
  exit 1
fi
