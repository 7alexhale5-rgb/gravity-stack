#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
NC='\033[0m'

# Xcode Command Line Tools
if xcode-select -p &>/dev/null; then
  echo -e "  ${GREEN}✓${NC} Xcode CLT already installed"
else
  echo "  Installing Xcode Command Line Tools..."
  xcode-select --install
  echo "  Waiting for installation to complete..."
  until xcode-select -p &>/dev/null; do sleep 5; done
fi

# Homebrew
if command -v brew &>/dev/null; then
  echo -e "  ${GREEN}✓${NC} Homebrew already installed: $(brew --version | head -1)"
else
  echo "  Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  eval "$(/opt/homebrew/bin/brew shellenv)"
fi

# Node.js via nvm
if command -v node &>/dev/null; then
  echo -e "  ${GREEN}✓${NC} Node.js already installed: $(node --version)"
else
  echo "  Installing nvm + Node.js 22..."
  if ! command -v nvm &>/dev/null; then
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
  fi
  nvm install 22
  nvm use 22
  nvm alias default 22
fi

# Python via pyenv
if command -v python3 &>/dev/null && python3 --version 2>&1 | grep -q "3.1[0-9]"; then
  echo -e "  ${GREEN}✓${NC} Python already installed: $(python3 --version)"
else
  echo "  Installing pyenv + Python 3.12..."
  brew install pyenv 2>/dev/null || true
  pyenv install 3.12 2>/dev/null || true
  pyenv global 3.12
fi

# Docker
if command -v docker &>/dev/null; then
  echo -e "  ${GREEN}✓${NC} Docker already installed: $(docker --version)"
else
  echo "  Installing Docker Desktop..."
  brew install --cask docker 2>/dev/null || echo "  Install Docker Desktop manually from docker.com"
fi

# Git
if command -v git &>/dev/null; then
  echo -e "  ${GREEN}✓${NC} Git already installed: $(git --version)"
else
  echo "  Installing Git..."
  brew install git
fi

# gh CLI
if command -v gh &>/dev/null; then
  echo -e "  ${GREEN}✓${NC} gh CLI already installed: $(gh --version | head -1)"
else
  echo "  Installing GitHub CLI..."
  brew install gh
fi
