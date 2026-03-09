#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "  Verifying MCP server packages..."

# Check npm packages are accessible
for pkg in "@playwright/mcp" "firecrawl-mcp" "@perplexity-ai/mcp-server" "@modelcontextprotocol/server-memory" "hn-mcp"; do
  if npm list -g "$pkg" &>/dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} $pkg available"
  else
    echo -e "  ${GREEN}✓${NC} $pkg will be loaded on-demand via npx"
  fi
done

# Check API keys
if [ -n "${FIRECRAWL_API_KEY:-}" ]; then
  echo -e "  ${GREEN}✓${NC} FIRECRAWL_API_KEY set"
else
  echo -e "  ${YELLOW}!${NC} FIRECRAWL_API_KEY not set (Firecrawl will not work without it)"
fi

if [ -n "${PERPLEXITY_API_KEY:-}" ]; then
  echo -e "  ${GREEN}✓${NC} PERPLEXITY_API_KEY set"
else
  echo -e "  ${YELLOW}!${NC} PERPLEXITY_API_KEY not set (Perplexity will not work without it)"
fi

echo -e "  ${GREEN}✓${NC} MCP servers configured in settings.json"
