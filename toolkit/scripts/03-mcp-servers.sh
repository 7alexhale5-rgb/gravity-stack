#!/usr/bin/env bash
# Register servers through Claude's supported config store, without overwriting existing entries.
set -euo pipefail
command -v claude >/dev/null || { echo "Claude CLI required for MCP registration" >&2; exit 1; }
registered() {
  # Inspect the supported user store without starting servers or printing config.
  python3 - "${CLAUDE_CONFIG_DIR:-$HOME}/.claude.json" "$1" <<'PY'
import json,sys
from pathlib import Path
path=Path(sys.argv[1])
if not path.exists(): sys.exit(1)
try:
    data=json.loads(path.read_text())
    servers=data.get('mcpServers', {})
    if not isinstance(servers,dict): sys.exit(2)
    entry=servers.get(sys.argv[2])
    if entry is None: sys.exit(1)
    if not isinstance(entry,dict): sys.exit(2)
    sys.exit(0 if any(isinstance(entry.get(k),str) and entry[k] for k in ('command','url')) else 2)
except (OSError,ValueError,AttributeError): sys.exit(2)
PY
}
register() {
  local name="$1"; shift
  local status=0
  registered "$name" || status=$?
  if [[ "$status" == 0 ]]; then
    echo "  Registered already: $name (preserved)"
  elif [[ "$status" != 1 ]]; then
    echo "  FAIL user config unreadable or invalid: $name (preserved)" >&2
    return 1
  else
    claude mcp add --scope user "$name" "$@" >/dev/null 2>&1 || { echo "  FAIL registration: $name" >&2; return 1; }
    registered "$name" || { echo "  FAIL registration read-back: $name" >&2; return 1; }
    echo "  Registered: $name"
  fi
}
register playwright --transport stdio -- npx -y @playwright/mcp@0.0.68
register firecrawl --transport stdio -- npx -y firecrawl-mcp@3.9.0
register perplexity --transport stdio -- npx -y @perplexity-ai/mcp-server@0.8.2
register memory --transport stdio --env "MEMORY_FILE_PATH=$HOME/.claude/memory/graph.json" -- npx -y @modelcontextprotocol/server-memory@2026.1.26
register hacker-news --transport stdio -- npx -y hn-mcp@1.0.0
# Public documentation only, opt-in; no OpenAI API key needed.
if [[ "${GRAVITY_INSTALL_OPENAI_DOCS:-0}" == 1 ]]; then
  register openai-docs --transport http https://developers.openai.com/mcp
fi
for key in FIRECRAWL_API_KEY PERPLEXITY_API_KEY; do
  if [[ -n "${!key:-}" ]]; then
    echo "  $key present in this shell; authentication remains unverified"
  else
    echo "  $key absent; launch Claude from a securely configured shell before using that service"
  fi
done
echo "  Registration checked. Restart Claude and test selected tools; connection and credentials are not proven here."
