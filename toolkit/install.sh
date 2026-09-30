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

DEV_PROTOCOL_REPO="https://github.com/7alexhale5-rgb/development-protocol.git"
DRY_RUN=0
ASSUME_YES=0
SKIP_DEV_PROTOCOL=0

usage() {
  cat <<EOF
Usage: bash toolkit/install.sh [--dry-run] [--yes] [--skip-dev-protocol]

  --dry-run            print what would happen, change nothing
  --yes, -y            answer yes to the optional development-protocol step
  --skip-dev-protocol  do not offer the optional development-protocol step
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --yes|-y) ASSUME_YES=1; shift ;;
    --skip-dev-protocol) SKIP_DEV_PROTOCOL=1; shift ;;
    --help|-h) usage; exit 0 ;;
    *) echo "unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

echo -e "${BOLD}╔══════════════════════════════════════╗${NC}"
echo -e "${BOLD}║   GRAVITY STACK — INSTALLER          ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════╝${NC}"
echo ""
if [[ $DRY_RUN -eq 1 ]]; then
  echo -e "${YELLOW}Dry run: nothing will be installed or changed.${NC}"
  echo ""
fi

# Check macOS
if [[ "$(uname)" != "Darwin" ]]; then
  echo -e "${RED}Error: Gravity Stack requires macOS.${NC}"
  exit 1
fi

# Check Apple Silicon
if [[ "$(uname -m)" != "arm64" ]]; then
  echo -e "${YELLOW}Warning: Apple Silicon (M1+) recommended.${NC}"
fi

run_phase() {
  local title="$1" script="$2"
  echo -e "${BOLD}${title}${NC}"
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "  would run: scripts/${script}"
  else
    bash "$SCRIPT_DIR/scripts/${script}"
  fi
  echo ""
}

run_phase "Phase 1: Foundation" "01-foundation.sh"
run_phase "Phase 2: Claude Code" "02-claude-code.sh"
run_phase "Phase 3: MCP Servers" "03-mcp-servers.sh"
run_phase "Phase 4: Hooks" "04-hooks.sh"
run_phase "Phase 5: Verification" "05-verify.sh"

# Optional: the development-protocol skills (spec, build, verify, close).
echo -e "${BOLD}Phase 6 (optional): Development process${NC}"
if [[ $SKIP_DEV_PROTOCOL -eq 1 ]]; then
  echo "  Skipped (--skip-dev-protocol)."
else
  answer="n"
  asked=0
  # Default to claude only; go both when this machine also has a Codex
  # skills root (~/.agents), so Codex users are not left out silently.
  dp_target="claude"
  [[ -d "$HOME/.agents" ]] && dp_target="both"
  if [[ $ASSUME_YES -eq 1 ]]; then
    answer="y"
  elif [[ $DRY_RUN -eq 1 ]]; then
    echo "  would ask: Install the development-protocol skills from ${DEV_PROTOCOL_REPO}? [y/N]"
  elif [[ -t 0 ]]; then
    asked=1
    read -r -p "  Install the development-protocol skills from ${DEV_PROTOCOL_REPO}? [y/N] " answer || answer="n"
  else
    echo "  No terminal to ask on. Skipping (re-run with --yes to install)."
  fi

  if [[ "$answer" =~ ^[Yy] ]]; then
    if [[ $DRY_RUN -eq 1 ]]; then
      echo "  would run: git clone --depth 1 ${DEV_PROTOCOL_REPO} <temp folder>"
      echo "  would run: ./install.sh --target ${dp_target} --yes (inside the clone), then delete the temp folder"
    else
      tmp_dir="$(mktemp -d)"
      trap 'rm -rf "$tmp_dir"' EXIT
      if git clone --quiet --depth 1 "$DEV_PROTOCOL_REPO" "$tmp_dir/development-protocol" \
        && (cd "$tmp_dir/development-protocol" && ./install.sh --target "$dp_target" --yes); then
        echo -e "  ${GREEN}✓${NC} development-protocol installed"
      else
        echo -e "  ${YELLOW}!${NC} development-protocol step failed. The rest of the install is fine."
        echo "    Install it by hand later: ${DEV_PROTOCOL_REPO}"
      fi
    fi
  elif [[ $asked -eq 1 ]]; then
    echo "  Skipped."
  fi
fi
echo ""

if [[ $DRY_RUN -eq 1 ]]; then
  echo -e "${GREEN}${BOLD}Dry run complete.${NC} Nothing was changed."
else
  echo -e "${GREEN}${BOLD}Installation complete!${NC}"
  echo -e "Run ${BOLD}claude${NC} to start using your AI-native environment."
fi
