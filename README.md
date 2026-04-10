# Knowledge Base System

A local-first knowledge base for Claude Code, Cursor, and the `kb` CLI.

The project now uses a **single local/remote web service backend**. Both the CLI and the MCP server act as clients of that service, which keeps indexing, search, source management, and progress tracking consistent.

## Current Architecture

```text
Claude Code / Cursor / kb CLI
            |
            | MCP stdio / CLI commands
            v
+---------------------------+
| MCP proxy / CLI client    |
| - kb.mcp.server           |
| - kb CLI                  |
+-------------+-------------+
              |
              | HTTP
              v
+---------------------------+
| KB Web Service            |
| - source registration     |
| - indexing orchestration  |
| - search                  |
| - status/progress         |
+------+------+-------------+
       |      |
       |      +--------------------+
       |                           |
       v                           v
+-------------------+   +----------------------+
| SQLite metadata   |   | Chroma vector store  |
| sources/documents |   | chunk embeddings     |
+-------------------+   +----------------------+
```

## What Works Today

- Local file and directory indexing
- GitHub repository indexing via `git clone`
- Single-page web indexing
- Sitemap-based site indexing
- Semantic search with Ollama embeddings + Chroma
- MCP integration for Claude Code and Cursor
- Local KB web service with CLI lifecycle commands
- Source progress tracking
- Reindex / update flows
- Remote service connection through `kb connect`

## Package Layout

The project now follows a `src` layout:

```text
src/kb/
├── cli/            # CLI entrypoint and command UX
├── client/         # Shared HTTP client used by CLI and MCP
├── core/           # Storage, indexing, retrieval, models
├── http/           # Web service app + local process manager
├── mcp/            # FastMCP proxy server
├── service/        # Service orchestration layer
├── sources/        # GitHub / local / web source adapters
├── config.py       # Config models and path resolution
└── presenters.py   # Shared text formatting
```

## Installation

### Prerequisites

1. Ollama with `nomic-embed-text`
2. Git

```bash
ollama pull nomic-embed-text
ollama serve
```

### Install from Python package

Python 3.10+ is required for this option.

```bash
pip install -e .
```

This installs:

```bash
kb
kb-http
kb-mcp
python -m kb.http
python -m kb.mcp
```

### Install prebuilt binaries

Python is not required for this option.

Published binary archives currently cover:

- macOS x64
- macOS arm64
- Linux x64
- Windows x64

macOS / Linux:

```bash
curl -fsSL https://raw.githubusercontent.com/zhiqli1993/knowledge-base/main/install.sh | sh
```

Windows PowerShell:

```powershell
irm https://raw.githubusercontent.com/zhiqli1993/knowledge-base/main/install.ps1 | iex
```

Linux arm64 is not published yet; use the Python package install on that platform for now.

## Default Config Path

The preferred config path is:

```bash
~/.kb/config.json
```

Legacy fallback is still supported:

```bash
~/.config/knowledge-base/config.json
```

Example:

```json
{
  "chroma": {
    "persist_directory": "~/.local/share/knowledge-base/chroma",
    "collection_name": "knowledge_base"
  },
  "ollama": {
    "host": "localhost",
    "port": 11434,
    "model": "nomic-embed-text",
    "timeout": 60
  },
  "local": {
    "allowed_paths": [
      "/Users/zhiqli/Documents",
      "/Users/zhiqli/workspace"
    ],
    "allow_unrestricted_paths": false
  },
  "service": {
    "host": "127.0.0.1",
    "port": 8864,
    "timeout_seconds": 30
  }
}
```

## CLI Overview

Core commands:

```bash
kb serve
kb stop
kb restart
kb logs
kb connect http://host:port
kb connect local

kb status
kb list
kb progress <source-id>
kb add-local <path>
kb add-url <url>
kb add-site <base-url> [max-pages]
kb add-repo <owner/repo> [branch]
kb search "query"
kb delete <source-id>
kb update <source-id|--all>
kb reindex <source-id|--all>
```

If `branch` is omitted for `kb add-repo`, the service detects the remote default branch automatically.

## MCP Setup

### Claude Code

Create `.mcp.json`:

```json
{
  "mcpServers": {
    "knowledge-base": {
      "command": "kb-mcp",
      "env": {
        "KNOWLEDGE_BASE_CONFIG": "/Users/your-user/.kb/config.json"
      }
    }
  }
}
```

### Cursor

Create `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "knowledge-base": {
      "command": "kb-mcp",
      "env": {
        "KNOWLEDGE_BASE_CONFIG": "/Users/your-user/.kb/config.json"
      }
    }
  }
}
```

Important:

- Install either the Python package or the prebuilt binary bundle first
- The MCP server now proxies the KB web service instead of accessing storage directly
- Start the local service with `kb serve` before using MCP tools locally
- `kb-mcp` is available from both the Python package install and the binary release install

## MCP Tools

Current MCP tools:

- `kb_add_local`
- `kb_add_repo`
- `kb_add_url`
- `kb_add_site`
- `kb_search`
- `kb_list`
- `kb_status`
- `kb_progress`
- `kb_update`
- `kb_reindex`
- `kb_delete`

## Validation Snapshot

Latest verified state:

- `pytest` → `98 passed`
- CLI web-service E2E validated locally
- MCP proxy E2E validated locally
- Local binary bundle smoke test validated on the current platform
- `kb serve/status/add-local/progress/search/connect/logs/delete/stop` verified
- GitHub Actions workflow: `.github/workflows/build.yml`
- GitHub release workflow: `.github/workflows/release.yml`

## Automation

- Push to `main` or open a pull request to run `.github/workflows/build.yml`
- Push a version tag such as `v0.1.0` to run `.github/workflows/release.yml`
- The release workflow rebuilds the package, validates the installed wheel in a clean environment, builds cross-platform `kb` / `kb-http` / `kb-mcp` binaries, and attaches all artifacts to the GitHub Release
- Release tags must match `pyproject.toml` exactly, for example package version `0.1.0` must be tagged as `v0.1.0`

## Development

```bash
pytest -q
pytest tests/unit -q
pytest tests/integration/test_mcp_server.py -q
pytest tests/e2e -q
```

## Related Docs

- `USAGE.md`
- `docs/testing.md`
- `docs/test-results.md`
- `docs/local-agent-design.md`
- `skill/SKILL.md`

## License

MIT
