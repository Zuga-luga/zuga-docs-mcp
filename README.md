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

## Install — one command

Clones, builds an isolated venv, installs deps, and registers with Claude Code
with your token + the venv's python **baked into the registration** (so the
server can't start tokenless — that's the `MCP error -32000` everyone hits).

**Windows (PowerShell):**

```powershell
irm https://raw.githubusercontent.com/Zuga-luga/zuga-docs-mcp/main/install.ps1 | iex
```

**macOS / Linux:**

```bash
curl -fsSL https://raw.githubusercontent.com/Zuga-luga/zuga-docs-mcp/main/install.sh | bash
```

It prompts for your token once. To skip the prompt, pass it as the first arg
(e.g. `./install.ps1 zdocs_xxx`) or set `$env:ZUGA_DOCS_TOKEN` first. Then
**restart Claude Code** and ask it to run `list_docs`.

<details>
<summary>Manual install (if you'd rather wire it yourself)</summary>

```bash
git clone https://github.com/Zuga-luga/zuga-docs-mcp.git && cd zuga-docs-mcp
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt   # Windows: .venv\Scripts\python.exe
```

Register, pointing `command` at the **venv's python** and putting the token in
the `env` block (NOT a bare `python` and NOT relying on shell env — both cause
-32000):

```bash
claude mcp add zuga-docs \
  -e ZUGA_DOCS_URL=https://zugabot.ai \
  -e ZUGA_DOCS_TOKEN=<your token> \
  -- /abs/path/zuga-docs-mcp/.venv/bin/python /abs/path/zuga-docs-mcp/zuga_docs_mcp.py
```

Or in `.mcp.json`:

```json
{
  "mcpServers": {
    "zuga-docs": {
      "command": "/abs/path/zuga-docs-mcp/.venv/bin/python",
      "args": ["/abs/path/zuga-docs-mcp/zuga_docs_mcp.py"],
      "env": {
        "ZUGA_DOCS_URL": "https://zugabot.ai",
        "ZUGA_DOCS_TOKEN": "your-token-here"
      }
    }
  }
}
```
</details>

## Tools

| Tool | What it does |
|------|--------------|
| `list_docs(filter="")` | List the docs shared with you (optional substring filter). |
| `fetch_doc(path)`      | Get one doc's full markdown by its path. |

Read-only. You cannot edit or publish docs through this server.
