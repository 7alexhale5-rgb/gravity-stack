#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

PASS=0
FAIL=0
CONFIG_ROOT="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"

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
import json, os, re, shlex, shutil, subprocess
from pathlib import Path
try:
    selected = Path(os.environ.get('CLAUDE_CONFIG_DIR') or str(Path.home() / '.claude'))
    root = selected.resolve()
    settings = json.loads((root / 'settings.json').read_text())
    if settings.get('disableAllHooks', False) is not False:
        raise SystemExit(1)
    gate = root / 'hooks/commit-gate.py'
    def matches_bash(matcher):
        # Claude uses exact alternatives or JavaScript RegExp.test, not Python regex.
        if matcher in ('', '*'):
            return True
        if re.fullmatch(r'[A-Za-z0-9_]+(?:\|[A-Za-z0-9_]+)*', matcher):
            return 'Bash' in matcher.split('|')
        script = "try {process.exit(new RegExp(process.argv[1]).test('Bash')?0:1)} catch {process.exit(2)}"
        result = subprocess.run(['node', '-e', script, matcher], capture_output=True, timeout=5)
        if result.returncode == 2:
            raise ValueError('invalid hook matcher')
        return result.returncode == 0
    def invokes_gate(command):
        args = shlex.split(command, posix=False)
        if not args:
            return False
        interpreter = args[0]
        if len(interpreter) >= 2 and interpreter[0] == interpreter[-1] and interpreter[0] in (chr(34), chr(39)):
            interpreter = interpreter[1:-1]
        if not re.fullmatch(r'python(?:3(?:\.\d+)?)?', Path(interpreter).name) or ("/" in interpreter and not Path(interpreter).is_absolute()):
            return False
        resolved = shutil.which(interpreter)
        if resolved is None or not Path(resolved).is_file() or not os.access(resolved, os.X_OK):
            return False
        position = 1
        while position < len(args) and args[position] in ('-u', '-B', '-I', '-E', '-s', '-S', '-O', '-OO'):
            position += 1
        if position < len(args) and args[position] == '--':
            position += 1
        # Recognize literal shell spellings, without expanding single-quoted variables.
        try:
            relative = str(gate.relative_to(Path.home().resolve()))
        except ValueError:
            relative = None
        absolute = str(gate)
        supported = {
            absolute, '"' + absolute + '"', "'" + absolute + "'",
        }
        spelled_gate = str(selected / 'hooks/commit-gate.py')
        if Path(spelled_gate).is_absolute():
            supported.update({spelled_gate, '"' + spelled_gate + '"', "'" + spelled_gate + "'"})
        if relative is not None:
            supported.update({
                '~/' + relative, '$HOME/' + relative, '${HOME}/' + relative,
                '"$HOME/' + relative + '"', '"${HOME}/' + relative + '"',
            })
        # shlex.quote's literal spelling handles spaces and apostrophes without
        # interpreting variables, substitutions, operators, or extra arguments.
        literal_command = ' '.join(args[:position]) + ' ' + shlex.quote(absolute)
        if command == literal_command:
            return True
        # The gate accepts no script arguments or shell composition. Suffixes can
        # mask its blocking exit status or run it in the background.
        return position == len(args) - 1 and args[position] in supported
    def invokes_handler(hook):
        # Current Claude handlers can filter calls or use an argv rather than a shell.
        # Only an unconditional, synchronous POSIX command is credited here.
        if 'if' in hook:
            return False
        if 'args' not in hook:
            return hook.get('shell', 'bash') == 'bash' and invokes_gate(hook.get('command', ''))
        args = hook['args']
        interpreter = hook.get('command', '')
        if not isinstance(args, list) or not all(isinstance(value, str) for value in args):
            return False
        if not re.fullmatch(r'python(?:3(?:\.\d+)?)?', Path(interpreter).name) or ('/' in interpreter and not Path(interpreter).is_absolute()):
            return False
        executable = shutil.which(interpreter)
        if executable is None or not Path(executable).is_file() or not os.access(executable, os.X_OK):
            return False
        position = 0
        while position < len(args) and args[position] in ('-u', '-B', '-I', '-E', '-s', '-S', '-O', '-OO'):
            position += 1
        if position < len(args) and args[position] == '--':
            position += 1
        return (position == len(args) - 1 and Path(args[position]).is_absolute()
                and Path(args[position]).resolve() == gate.resolve())
    registered = False
    for group in settings.get('hooks', {}).get('PreToolUse', []):
        if not matches_bash(group.get('matcher', '')):
            continue
        for hook in group.get('hooks', []):
            timeout = hook.get('timeout')
            if (hook.get('type') == 'command' and invokes_handler(hook)
                    and type(timeout) in (int, float) and timeout >= 70
                    and hook.get('async', False) is False
                    and hook.get('asyncRewake', False) is False):
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
check "Settings found" 'test -f "$CONFIG_ROOT/settings.json"' 'printf "%s" "$CONFIG_ROOT/settings.json"'
check "Hooks directory" 'test -d "$CONFIG_ROOT/hooks"' 'printf "%s" "$CONFIG_ROOT/hooks/"'
check "Memory directory" 'test -d "$CONFIG_ROOT/memory"' 'printf "%s" "$CONFIG_ROOT/memory/"'
echo ""

check "Commit gate file and registration" "commit_gate_registered" "echo 'read back from settings'"

TOTAL=$((PASS + FAIL))
echo -e "${BOLD}Results: ${GREEN}${PASS}/${TOTAL} passed${NC}"

if [ "$FAIL" -eq 0 ]; then
  echo -e "\n${GREEN}${BOLD}Status: FOUNDATION AND COMMIT REGISTRATION CHECKS PASSED${NC}"
else
  echo -e "\n${RED}${BOLD}Status: ${FAIL} CHECK(S) FAILED${NC}"
  echo "  For commit-gate failures, preserve your existing gate, compare it with toolkit/configs/commit-gate.py, and install the reviewed current version."
  echo '  Set only that PreToolUse command hook to "timeout": 70; keep its blocking exit status (no || true).'
  echo "  Existing settings and gate files are preserved; rerunning setup alone does not update them."
  exit 1
fi

echo "Live hook firing, agent selection, optional CARL and MCP connections still need separate checks."
