#!/usr/bin/env bash
set -euo pipefail

# Gravity Stack — Master Bootstrap
# Installs and configures an AI-native development environment.
# Safe to re-run (idempotent).

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BOLD}╔══════════════════════════════════════╗${NC}"
echo -e "${BOLD}║   GRAVITY STACK — INSTALLER          ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════╝${NC}"
echo ""

# Check macOS
if [[ "$(uname)" != "Darwin" ]]; then
  echo -e "${RED}Error: Gravity Stack requires macOS.${NC}"
  exit 1
fi

# Check Apple Silicon
if [[ "$(uname -m)" != "arm64" ]]; then
  echo -e "${YELLOW}Warning: Apple Silicon (M1+) recommended.${NC}"
fi

echo -e "${BOLD}Phase 1: Foundation${NC}"
bash "$SCRIPT_DIR/scripts/01-foundation.sh"
echo ""

echo -e "${BOLD}Phase 2: Claude Code${NC}"
bash "$SCRIPT_DIR/scripts/02-claude-code.sh"
echo ""

echo -e "${BOLD}Phase 3: MCP Servers${NC}"
bash "$SCRIPT_DIR/scripts/03-mcp-servers.sh"
echo ""

echo -e "${BOLD}Phase 4: Hooks${NC}"
bash "$SCRIPT_DIR/scripts/04-hooks.sh"
echo ""

echo -e "${BOLD}Phase 5: Verification${NC}"
bash "$SCRIPT_DIR/scripts/05-verify.sh"
echo ""

echo -e "${GREEN}${BOLD}Installation complete!${NC}"
echo -e "Run ${BOLD}claude${NC} to start using your AI-native environment."
