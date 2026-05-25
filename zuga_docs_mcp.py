"""Zuga Docs MCP.

A stdio MCP server that lets a teammate's MCP client (Claude Code, Cursor, etc.)
read the plans & specs Buga has shared with them. Each tool call is a read-only
HTTPS request to ZugaApp's /api/docs/* endpoints, authenticated with a personal
docs token the teammate mints at zugabot.ai (ZugaId login -> mint).

The teammate only ever sees docs explicitly granted to them; the server filters
by grant and the docs themselves live in a private repo they never touch.

Config (env):
    ZUGA_DOCS_URL    Base URL of ZugaApp            (default: https://zugabot.ai)
    ZUGA_DOCS_TOKEN  Your docs token (zdocs/zcat_*) (required)

Run:
    python zuga_docs_mcp.py          # stdio MCP server

Register with Claude Code:
    claude mcp add zuga-docs -- python /absolute/path/to/zuga_docs_mcp.py
"""

from __future__ import annotations

import os
import sys

import httpx
from mcp.server.fastmcp import FastMCP

BASE_URL = os.environ.get("ZUGA_DOCS_URL", "https://zugabot.ai").rstrip("/")
TOKEN = os.environ.get("ZUGA_DOCS_TOKEN", "").strip()

if not TOKEN:
    print(
        "ERROR: set ZUGA_DOCS_TOKEN before starting. Mint one at "
        f"{BASE_URL} (log in -> Docs access -> Mint token).",
        file=sys.stderr,
    )
    sys.exit(2)

HEADERS = {"Authorization": f"Bearer {TOKEN}"}

mcp = FastMCP("zuga-docs")


def _check(r) -> None:
    if r.status_code == 401:
        raise RuntimeError("Auth rejected — check ZUGA_DOCS_TOKEN (re-mint at zugabot.ai if needed).")
    if r.status_code == 403:
        raise RuntimeError("Not allowed — you can only act on issues assigned to you.")
    if r.status_code == 404:
        raise RuntimeError("Not found, or you don't have access.")
    if r.status_code == 400:
        raise RuntimeError("Your account isn't mapped to a GitHub login yet — ask Buga to set it.")
    if r.status_code == 503:
        raise RuntimeError("Service not configured on the server yet.")
    r.raise_for_status()


async def _get(path: str, params: dict | None = None) -> dict:
    """GET one /api endpoint, mapping auth/404 to clean messages."""
    async with httpx.AsyncClient(timeout=30.0) as http:
        r = await http.get(f"{BASE_URL}{path}", headers=HEADERS, params=params or {})
    _check(r)
    return r.json()


async def _post(path: str, payload: dict) -> dict:
    """POST one /api endpoint."""
    async with httpx.AsyncClient(timeout=30.0) as http:
        r = await http.post(f"{BASE_URL}{path}", headers=HEADERS, json=payload)
    _check(r)
    return r.json()


@mcp.tool()
async def list_docs(filter: str = "") -> str:
    """List the plans/specs shared with you.

    Args:
        filter: optional case-insensitive substring; matches title or path.
    """
    data = await _get("/api/docs/list")
    docs = data.get("docs", [])
    if filter:
        f = filter.lower()
        docs = [d for d in docs if f in d.get("path", "").lower() or f in d.get("title", "").lower()]
    if not docs:
        return "No docs shared with you yet." if not filter else f"No docs match '{filter}'."
    lines = ["| kind  | path | size |", "|-------|------|------|"]
    for d in sorted(docs, key=lambda x: x["path"], reverse=True):
        lines.append(f"| {d.get('kind','')} | `{d['path']}` | {d.get('bytes',0)} B |")
    lines.append("\nFetch one with `fetch_doc(path)`.")
    return "\n".join(lines)


@mcp.tool()
async def fetch_doc(path: str) -> str:
    """Fetch one shared doc's full markdown by its path (from list_docs).

    Args:
        path: e.g. "plans/2026-05-25-foo.md" (relative path shown by list_docs).
    """
    data = await _get("/api/docs/get", params={"path": path})
    return data.get("content_markdown", "")


# ── GitHub issues (assigned to you) ──────────────────────────────────────────


@mcp.tool()
async def list_issues(state: str = "open") -> str:
    """List the GitHub issues assigned to you across Zuga-Technologies.

    Args:
        state: "open" (default), "closed", or "all".
    """
    data = await _get("/api/team/issues", params={"state": state})
    issues = data.get("issues", [])
    if not issues:
        return f"No {state} issues assigned to you."
    lines = ["| repo | # | state | title |", "|------|---|-------|-------|"]
    for it in issues:
        lines.append(f"| `{it['repo']}` | {it['number']} | {it['state']} | {it['title']} |")
    lines.append("\nOpen one with `read_issue(repo, number)`.")
    return "\n".join(lines)


@mcp.tool()
async def read_issue(repo: str, number: int) -> str:
    """Read one assigned issue with its comments.

    Args:
        repo: "ZugaCore" or "Zuga-Technologies/ZugaCore".
        number: the issue number.
    """
    d = await _get("/api/team/issue", params={"repo": repo, "number": number})
    out = [f"# {d['title']}  ({d['repo']}#{d['number']}, {d['state']})", "", d["body"] or "_no body_"]
    if d.get("comments"):
        out.append("\n## Comments")
        for c in d["comments"]:
            out.append(f"\n**{c['author']}** ({c['at']}):\n{c['body']}")
    out.append(f"\n{d['url']}")
    return "\n".join(out)


@mcp.tool()
async def comment_issue(repo: str, number: int, body: str) -> str:
    """Add a comment to an issue assigned to you (signed with your name).

    Args:
        repo: "ZugaCore" or "Zuga-Technologies/ZugaCore".
        number: the issue number.
        body: comment markdown.
    """
    d = await _post("/api/team/issue/comment", {"repo": repo, "number": number, "body": body})
    return f"Comment posted: {d.get('url')}"


@mcp.tool()
async def close_issue(repo: str, number: int, comment: str = "") -> str:
    """Close an issue assigned to you, with an optional closing note.

    Args:
        repo: "ZugaCore" or "Zuga-Technologies/ZugaCore".
        number: the issue number.
        comment: optional closing comment.
    """
    payload = {"repo": repo, "number": number}
    if comment:
        payload["comment"] = comment
    await _post("/api/team/issue/close", payload)
    return f"Closed {repo}#{number}."


@mcp.tool()
async def create_issue(repo: str, title: str, body: str = "") -> str:
    """Open a new issue in an org repo, assigned to you.

    Args:
        repo: "ZugaCore" or "Zuga-Technologies/ZugaCore".
        title: issue title.
        body: issue body markdown.
    """
    d = await _post("/api/team/issue", {"repo": repo, "title": title, "body": body})
    return f"Created {repo}#{d.get('number')}: {d.get('url')}"


if __name__ == "__main__":
    mcp.run()
