#!/usr/bin/env bash
# One-command project setup for new developers
set -euo pipefail

echo "=== oh-my-cloud-skills Setup ==="

# Check prerequisites
command -v python3 >/dev/null 2>&1 || { echo "ERROR: python3 required"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "ERROR: node required"; exit 1; }
command -v git >/dev/null 2>&1 || { echo "ERROR: git required"; exit 1; }

echo "Prerequisites: OK"

# Create .env from example if needed
if [ ! -f .env ] && [ -f .env.example ]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

# Install doc-sites (Docusaurus) dependencies
if [ -d doc-sites ] && [ -f doc-sites/package.json ]; then
  echo "Installing doc-sites dependencies..."
  cd doc-sites
  if command -v pnpm >/dev/null 2>&1; then
    pnpm install
  elif command -v yarn >/dev/null 2>&1; then
    yarn install
  else
    npm install
  fi
  cd ..
fi

# Install git hooks
if [ -f scripts/install-hooks.sh ]; then
  bash scripts/install-hooks.sh
fi

# Make claude hooks executable
chmod +x .claude/hooks/*.sh 2>/dev/null || true

# Validate plugins
echo "Validating plugins..."
python3 scripts/test-plugins.py 2>/dev/null || echo "Plugin validation skipped"

echo ""
echo "Setup complete! Try:"
echo "  claude --plugin-dir ./plugins/aws-content-plugin"
echo "  claude --plugin-dir ./plugins/aws-ops-plugin"
