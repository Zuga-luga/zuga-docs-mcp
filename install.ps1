# Zuga Docs MCP — one-shot installer (Windows PowerShell)
#
#   Run from anywhere:
#     irm https://raw.githubusercontent.com/Zuga-luga/zuga-docs-mcp/main/install.ps1 | iex
#   ...or from a clone:
#     ./install.ps1
#
# Creates an isolated venv, installs deps, asks for your docs token once, and
# registers the server with Claude Code WITH the token + the venv's python baked
# into the registration — so it can never start tokenless (the -32000 cause).

$ErrorActionPreference = 'Stop'

# Resolve the repo dir whether run from a clone or piped from the web.
$RepoDir = if ($PSScriptRoot) { $PSScriptRoot } else { Join-Path $HOME 'zuga-docs-mcp' }

if (-not (Test-Path (Join-Path $RepoDir 'zuga_docs_mcp.py'))) {
    Write-Host '==> Cloning zuga-docs-mcp...' -ForegroundColor Cyan
    git clone https://github.com/Zuga-luga/zuga-docs-mcp.git $RepoDir
}
Set-Location $RepoDir

$Py = Get-Command python -ErrorAction SilentlyContinue
if (-not $Py) { throw 'python not found on PATH. Install Python 3.11+ first.' }

Write-Host '==> Creating venv + installing deps...' -ForegroundColor Cyan
python -m venv .venv
$VenvPy = Join-Path $RepoDir '.venv\Scripts\python.exe'
& $VenvPy -m pip install --quiet --upgrade pip
& $VenvPy -m pip install --quiet -r requirements.txt

# Token: arg > env > prompt.
$Token = if ($args.Count -ge 1) { $args[0] } elseif ($env:ZUGA_DOCS_TOKEN) { $env:ZUGA_DOCS_TOKEN } else {
    Write-Host ''
    Write-Host 'Mint a docs token at https://zugabot.ai -> Docs access -> Mint token' -ForegroundColor Yellow
    (Read-Host 'Paste your ZUGA_DOCS_TOKEN').Trim()
}
if (-not $Token) { throw 'No token provided. Re-run with: ./install.ps1 <token>' }

$Server = Join-Path $RepoDir 'zuga_docs_mcp.py'

Write-Host '==> Registering with Claude Code (token + python baked in)...' -ForegroundColor Cyan
claude mcp remove zuga-docs 2>$null | Out-Null
claude mcp add zuga-docs `
    -e "ZUGA_DOCS_URL=https://zugabot.ai" `
    -e "ZUGA_DOCS_TOKEN=$Token" `
    -- "$VenvPy" "$Server"

Write-Host ''
Write-Host 'Done. Restart Claude Code, then ask it to call list_docs.' -ForegroundColor Green
