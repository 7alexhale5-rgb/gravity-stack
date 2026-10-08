#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
NC='\033[0m'
CONFIG_ROOT="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"

# Claude Code CLI
if command -v claude &>/dev/null; then
  echo -e "  ${GREEN}✓${NC} Claude Code already installed: $(claude --version 2>/dev/null || echo 'installed')"
else
  echo "  Installing Claude Code CLI..."
  npm install -g @anthropic-ai/claude-code
fi

# Directory structure
for dir in hooks memory backups; do
  if [ -d "$CONFIG_ROOT/$dir" ]; then
    echo -e "  ${GREEN}✓${NC} $CONFIG_ROOT/$dir/ exists"
  else
    mkdir -p "$CONFIG_ROOT/$dir"
    echo -e "  ${GREEN}✓${NC} Created $CONFIG_ROOT/$dir/"
  fi
done

# Copy template settings if no settings exist
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ ! -f "$CONFIG_ROOT/settings.json" ]; then
  echo "  Copying template settings.json..."
  python3 - "$SCRIPT_DIR/configs/settings.json" "$CONFIG_ROOT" <<'PY'
import json, shlex, sys
from pathlib import Path
root = Path(sys.argv[2]).resolve()
settings = json.loads(Path(sys.argv[1]).read_text())
for group in settings['hooks']['PreToolUse']:
    for hook in group['hooks']:
        if hook.get('command') in ('python3 $HOME/.claude/hooks/commit-gate.py', 'python3 \"$HOME/.claude/hooks/commit-gate.py\"'):
            hook['command'] = 'python3 ' + shlex.quote(str(root / 'hooks/commit-gate.py'))
for group in settings['hooks']['PreCompact']:
    for hook in group['hooks']:
        if hook.get('command', '').startswith('mkdir -p ~/.claude/backups && cp ~/.claude/current-session.jsonl '):
            backup = shlex.quote(str(root / 'backups'))
            session = shlex.quote(str(root / 'current-session.jsonl'))
            hook['command'] = f'mkdir -p {backup} && cp {session} {backup}/session-$(date +%Y%m%d-%H%M%S).jsonl'
with (root / 'settings.json').open('x') as output:
    json.dump(settings, output, indent=2)
    output.write('\n')
PY
  echo -e "  ${GREEN}✓${NC} Settings configured"
else
  echo -e "  ${GREEN}✓${NC} Settings already exist (not overwriting)"
fi
