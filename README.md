# Knowledge Base System

A local-first knowledge extraction and retrieval system that indexes local folders/files, GitHub repositories, documentation sites, and web pages into a local vector database for semantic search from Claude Code, Cursor, or the CLI.

## Features

- **Multi-Source Support**: local files/directories, GitHub repos, single web pages, entire websites via sitemap
- **Smart Chunking**: Header-aware markdown chunking, sliding window for plain text
- **Local Embeddings**: Ollama (nomic-embed-text) for free, local vector generation
- **Semantic Search**: ChromaDB for vector storage and retrieval
- **Claude Code + Cursor Integration**: FastMCP server with `kb_*` tools
- **Pattern-Based Filtering**: Include/exclude file patterns for GitHub repos
- **Local Metadata Tracking**: Indexed timestamps plus document/chunk counts per source

## Installation

### Prerequisites

1. **Python 3.10+**
2. **Ollama** (for embeddings)

```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Pull the embedding model
ollama pull nomic-embed-text

# Start Ollama server
ollama serve
```

3. **Install Dependencies**
```bash
pip install -e .
```

This installs the local CLI command:

```bash
kb
kb status
```

## Usage

### MCP tools

The server now exposes these tools:

1. `kb_add_local` - Add a local file or directory
2. `kb_add_repo` - Add a GitHub repository
3. `kb_add_url` - Add a web page
4. `kb_add_site` - Add an entire website
5. `kb_search` - Search indexed content
6. `kb_list` - List sources
7. `kb_status` - Show statistics
8. `kb_delete` - Delete a source and its vectors

### Claude Code project config

Create `.mcp.json`:

```json
{
  "mcpServers": {
    "knowledge-base": {
      "command": "python3",
      "args": ["-m", "kb.mcp.server"],
      "env": {
        "KNOWLEDGE_BASE_CONFIG": "~/.kb/config.json"
      }
    }
  }
}
```

### Cursor project config

Create `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "knowledge-base": {
      "command": "python3",
      "args": ["-m", "kb.mcp.server"],
      "env": {
        "KNOWLEDGE_BASE_CONFIG": "~/.kb/config.json"
      }
    }
  }
}
```

### Local path safety

`kb_add_local` is scoped by `local.allowed_paths` in config. If you do not configure it, the server defaults to the current working directory as the allowed root.

```json
{
  "local": {
    "allowed_paths": [
      "/Users/zhiqli/Documents",
      "/Users/zhiqli/workspace"
    ],
    "allow_unrestricted_paths": false
  }
}
```

See `USAGE.md`, `skill/SKILL.md`, and `docs/local-agent-design.md` for more detail.

## Development

```bash
# Run tests
pytest

# With coverage
pytest --cov=kb

# E2E tests
pytest tests/e2e/ -v
```

## Current validation snapshot

- `tests/unit/test_indexer.py`
- `tests/unit/test_storage.py`
- `tests/unit/test_retriever.py`
- `tests/integration/test_mcp_server.py`

Latest targeted run: **26/26 passing**

## License

MIT
