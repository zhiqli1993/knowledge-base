# Local Agent Knowledge Base Design

## Goal

Build a local-first knowledge base that can be used from Claude Code, Cursor, and the `kb` CLI while keeping a single source of truth for indexing and retrieval.

## Current Architecture

The project has moved from direct CLI/MCP access to a service-oriented model.

```text
Clients
  - kb CLI
  - Claude Code via MCP
  - Cursor via MCP

        |
        v
Proxy / client layer
  - kb.cli.main
  - kb.mcp.server
  - kb.client.http

        |
        v
KB Web Service
  - kb.http.app
  - kb.service.core

        |
        v
Core pipeline
  - kb.core.storage
  - kb.core.indexer
  - kb.core.retriever
  - kb.sources.*

        |
        +--> SQLite metadata
        +--> Chroma vectors
```

## Why This Design

### Single backend authority

Both CLI and MCP now use the same backend, which avoids:

- duplicated business logic
- CLI/MCP behavior drift
- separate progress implementations
- conflicting direct writes from multiple entrypoints

### Clean package boundaries

- `kb/core`: indexing, retrieval, persistence
- `kb/service`: orchestration
- `kb/http`: service runtime and local process management
- `kb/client`: shared HTTP client
- `kb/cli`: human-facing command interface
- `kb/mcp`: AI-facing MCP proxy
- `kb/sources`: GitHub / web / local adapters

## Data Model Notes

`Source` metadata now includes progress-oriented fields used by both CLI and MCP:

- `progress_phase`
- `progress_message`
- `progress_total`
- `progress_processed`
- `progress_updated_at`

This allows a single `kb progress` / `kb_progress` view without adding a second progress store.

## Local Service Lifecycle

The local service is controlled by:

- `kb serve`
- `kb stop`
- `kb restart`
- `kb logs`

State is stored under `~/.kb/`.

## Remote Connection Model

CLI can target a remote KB service with:

```bash
kb connect http://host:port
```

and return to local mode with:

```bash
kb connect local
```

Important: when connected to a remote service, `add-local` refers to a path on the remote host.

## Current Non-Goals

Not implemented yet:

- authentication / authz
- persistent distributed job queue
- file watching
- binary parsers beyond the current text-first pipeline
