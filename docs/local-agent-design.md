# Local Agent Knowledge Base Design

## Goal

Turn the existing local MCP knowledge base into a practical local-first system that can be used directly from Claude Code and Cursor without any hosted dependencies beyond the optional local embedding runtime.

## Scope of this slice

- Add local file and directory ingestion.
- Expose local ingestion through MCP and CLI entrypoints.
- Keep storage local with SQLite metadata and Chroma vectors.
- Document client configuration for Claude Code and Cursor.

## Architecture

```text
Claude Code / Cursor / CLI
            |
            | MCP stdio / local CLI
            v
+---------------------------+
| FastMCP Knowledge Server  |
| kb_add_local / kb_search  |
| kb_list / kb_status       |
+-------------+-------------+
              |
              v
+---------------------------+
| Indexer Orchestrator      |
| source -> chunk -> embed  |
| -> store                  |
+------+------+-------------+
       |      |
       |      +--------------------+
       |                           |
       v                           v
+-------------------+   +----------------------+
| Source adapters   |   | Retrieval layer      |
| local / github /  |   | Chroma similarity    |
| web               |   | search + formatting  |
+---------+---------+   +----------------------+
          |
          v
+-------------------+   +----------------------+
| SQLite metadata   |   | Chroma vector store  |
| sources/documents |   | chunk embeddings     |
+-------------------+   +----------------------+
```

## Design decisions

### 1. Local source model

Use the existing `SourceType.LOCAL` and treat `Source.url` as the resolved absolute filesystem path.

Why:

- avoids introducing a second path field
- keeps local sources consistent with other source registrations
- makes list/status output immediately useful

### 2. Local source ingestion

Add a local source adapter that:

- accepts a file or directory path
- recursively scans directories
- applies include/exclude glob filters for directories
- skips oversized or unreadable files
- returns the existing `FileInfo` shape so the rest of the pipeline stays shared

### 3. MCP interface

Add `kb_add_local(path, include=None, exclude=None)` so AI clients can register local content with one tool call.

Expected behavior:

- normalize path to an absolute path
- reject missing paths early
- reject paths outside configured local allowlists
- use a stable `local:<absolute-path>` source id
- index asynchronously like the existing repo/url/site tools

### 4. CLI interface

Add `kb add-local <path>` for local testing and manual operation.

This keeps non-MCP troubleshooting simple and mirrors the MCP tool.

### 5. Metadata and deletion

As part of this slice, make source metadata more trustworthy:

- persist `last_indexed_at`
- persist `document_count`
- persist `chunk_count`

Deletion should also remove vector chunks for the source, not only SQLite rows.

### 6. Local path safety

Because MCP tools can be called by agents, local indexing must not implicitly grant access to arbitrary host files.

Policy in this slice:

- allow unrestricted local indexing only when `local.allow_unrestricted_paths=true`
- otherwise require `local.allowed_paths`, or fall back to the server working directory
- reject paths outside the approved roots before indexing starts

## Data flow

### Add local directory

1. Client calls `kb_add_local("/path/to/project")`
2. Server creates `Source(id="local:/path/to/project", type=LOCAL, url="/path/to/project")`
3. Indexer scans files, chunks content, generates embeddings, stores metadata and vectors
4. Source status moves `pending -> indexing -> ready`
5. Search can immediately retrieve local chunks

### Delete source

1. Client calls `kb_delete(source_id)`
2. Server removes Chroma vectors by `source_id`
3. Server removes SQLite source/documents

## Client integration

### Claude Code

- project config: `.mcp.json`
- global config: `~/.claude.json`

### Cursor

- project config: `.cursor/mcp.json`
- global config: `~/.cursor/mcp.json`

Both clients can launch the same local Python stdio server.

## Non-goals for this slice

- file watching / automatic reindex
- hybrid BM25 + vector retrieval
- ACL / multi-user permissions
- binary document parsing beyond the current text-oriented pipeline

## Future extensions

- incremental reindex based on file hashes
- native local PDF/doc parsing
- background queue persistence
- richer fetch tools (`kb_get_document`, `kb_show_source`)
