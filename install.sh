#!/usr/bin/env bash
# Zuga Docs MCP — one-shot installer (macOS / Linux)
#
#   Run from anywhere:
#     curl -fsSL https://raw.githubusercontent.com/Zuga-luga/zuga-docs-mcp/main/install.sh | bash
#   ...or from a clone:
#     ./install.sh [token]
#
# Creates an isolated venv, installs deps, asks for your docs token once, and
# registers the server with Claude Code WITH the token + the venv's python baked
# into the registration — so it can never start tokenless (the -32000 cause).
set -euo pipefail

# Resolve repo dir whether run from a clone or piped from the web.
if [ -n "${BASH_SOURCE[0]:-}" ] && [ -f "$(dirname "${BASH_SOURCE[0]}")/zuga_docs_mcp.py" ]; then
  REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
else
  REPO_DIR="$HOME/zuga-docs-mcp"
  if [ ! -f "$REPO_DIR/zuga_docs_mcp.py" ]; then
    echo "==> Cloning zuga-docs-mcp..."
    git clone https://github.com/Zuga-luga/zuga-docs-mcp.git "$REPO_DIR"
  fi
fi
cd "$REPO_DIR"

PYBIN="$(command -v python3 || command -v python)"
[ -n "$PYBIN" ] || { echo "python3 not found. Install Python 3.11+ first." >&2; exit 1; }

echo "==> Creating venv + installing deps..."
"$PYBIN" -m venv .venv
VENV_PY="$REPO_DIR/.venv/bin/python"
"$VENV_PY" -m pip install --quiet --upgrade pip
"$VENV_PY" -m pip install --quiet -r requirements.txt

# Token: arg > env > prompt.
TOKEN="${1:-${ZUGA_DOCS_TOKEN:-}}"
if [ -z "$TOKEN" ]; then
  echo
  echo "Mint a docs token at https://zugabot.ai -> Docs access -> Mint token"
  read -r -p "Paste your ZUGA_DOCS_TOKEN: " TOKEN
fi
[ -n "$TOKEN" ] || { echo "No token provided. Re-run with: ./install.sh <token>" >&2; exit 1; }

echo "==> Registering with Claude Code (token + python baked in)..."
claude mcp remove zuga-docs >/dev/null 2>&1 || true
claude mcp add zuga-docs \
  -e "ZUGA_DOCS_URL=https://zugabot.ai" \
  -e "ZUGA_DOCS_TOKEN=$TOKEN" \
  -- "$VENV_PY" "$REPO_DIR/zuga_docs_mcp.py"

echo
echo "Done. Restart Claude Code, then ask it to call list_docs."
