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
import json, os, re, shlex, subprocess
from pathlib import Path
try:
    settings = json.loads((Path.home() / '.claude/settings.json').read_text())
    gate = Path.home() / '.claude/hooks/commit-gate.py'
    def matches_bash(matcher):
        # Claude uses exact alternatives or JavaScript RegExp.test, not Python regex.
        if matcher in ('', '*'):
            return True
        if re.fullmatch(r'[A-Za-z0-9_ ,|\-]+', matcher):
            return any(name.strip() == 'Bash' for name in re.split(r'[|,]', matcher))
        script = "try {process.exit(new RegExp(process.argv[1]).test('Bash')?0:1)} catch {process.exit(2)}"
        result = subprocess.run(['node', '-e', script, matcher], capture_output=True, timeout=5)
        if result.returncode == 2:
            raise ValueError('invalid hook matcher')
        return result.returncode == 0
    def invokes_gate(command):
        args = shlex.split(command, posix=False)
        if not args or not re.fullmatch(r'python(?:3(?:\.\d+)?)?', Path(args[0]).name):
            return False
        position = 1
        while position < len(args) and args[position] in ('-u', '-B', '-I', '-E', '-s', '-S', '-O', '-OO'):
            position += 1
        if position < len(args) and args[position] == '--':
            position += 1
        # Recognize literal shell spellings, without expanding single-quoted variables.
        relative = str(gate.relative_to(Path.home()))
        absolute = str(gate)
        supported = {
            absolute, '"' + absolute + '"', "'" + absolute + "'",
            '~/' + relative, '$HOME/' + relative, '${HOME}/' + relative,
            '"$HOME/' + relative + '"', '"${HOME}/' + relative + '"',
        }
        return position < len(args) and args[position] in supported
    registered = False
    for group in settings.get('hooks', {}).get('PreToolUse', []):
        if not matches_bash(group.get('matcher', '')):
            continue
        for hook in group.get('hooks', []):
            if hook.get('type') == 'command' and invokes_gate(hook.get('command', '')):
                registered = True
    raise SystemExit(0 if gate.is_file() and registered else 1)
except (OSError, ValueError, TypeError, AttributeError, subprocess.SubprocessError):
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
