# Zuga Docs MCP

A tiny stdio MCP server that lets you read the plans & specs the Zuga
Technologies team has shared with you — straight from Claude Code (or Cursor,
etc.). You only ever see docs explicitly shared with your account.

```
Claude Code ──stdio MCP──► zuga_docs_mcp.py ──HTTPS──► zugabot.ai/api/docs/*
   (your PC)                   (your PC)                  (read-only, grant-gated)
```

## What you need

1. A ZugaId login at https://zugabot.ai (the same account Buga added you to).
2. A **docs token**: log in, open **Docs access**, click **Mint token**. Copy
   it once — it is shown only one time.

## Install

```bash
git clone https://github.com/Zuga-luga/zuga-docs-mcp.git
cd zuga-docs-mcp

python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell:
.venv\Scripts\activate

pip install -r requirements.txt
```

## Configure

Set two environment variables (keep the token out of git — use your OS keychain
or a local `.env`):

```bash
export ZUGA_DOCS_URL=https://zugabot.ai     # only override if self-hosted
export ZUGA_DOCS_TOKEN=<your minted token>
```

## Register with Claude Code

```bash
claude mcp add zuga-docs -- python /absolute/path/to/zuga_docs_mcp.py
```

Or add to your `.mcp.json`:

```json
{
  "mcpServers": {
    "zuga-docs": {
      "command": "python",
      "args": ["/absolute/path/to/zuga-docs-mcp/zuga_docs_mcp.py"],
      "env": {
        "ZUGA_DOCS_URL": "https://zugabot.ai",
        "ZUGA_DOCS_TOKEN": "your-token-here"
      }
    }
  }
}
```

## Tools

| Tool | What it does |
|------|--------------|
| `list_docs(filter="")` | List the docs shared with you (optional substring filter). |
| `fetch_doc(path)`      | Get one doc's full markdown by its path. |

Read-only. You cannot edit or publish docs through this server.
