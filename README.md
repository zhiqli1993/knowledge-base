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

1. Python 3.10+
2. Ollama with `nomic-embed-text`
3. Git

```bash
ollama pull nomic-embed-text
ollama serve
```

### Install

```bash
pip install -e .
```

This installs:

```bash
kb
python -m kb.http
python -m kb.mcp.server
```

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

## MCP Setup

### Claude Code

Create `.mcp.json`:

```json
{
  "mcpServers": {
    "knowledge-base": {
      "command": "python3",
      "args": ["-m", "kb.mcp.server"],
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
      "command": "python3",
      "args": ["-m", "kb.mcp.server"],
      "env": {
        "KNOWLEDGE_BASE_CONFIG": "/Users/your-user/.kb/config.json"
      }
    }
  }
}
```

Important:

- Install the package first with `pip install -e .`
- The MCP server now proxies the KB web service instead of accessing storage directly
- Start the local service with `kb serve` before using MCP tools locally

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

- `pytest` → `77 passed`
- CLI web-service E2E validated locally
- MCP proxy E2E validated locally
- `kb serve/status/add-local/progress/search/connect/logs/delete/stop` verified

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
