# Skill: knowledge-base

This skill provides commands for the Knowledge Base System - a local-first knowledge extraction and retrieval system that indexes local files/directories, GitHub repositories, documentation sites, and web pages into a local vector database.

## Commands

### /kb-add-repo <repo-url>
Add a GitHub repository to the knowledge base.

**Usage:**
- `/kb-add-repo owner/repo` - Short format
- `/kb-add-repo https://github.com/owner/repo` - Full URL

**Examples:**
- `/kb-add-repo anthropics/anthropic-sdk-python`
- `/kb-add-repo https://github.com/langchain-ai/langchain`

### /kb-add-url <url>
Add a single web page to the knowledge base.

**Usage:**
- `/kb-add-url <url>` - Any web page URL

**Example:**
- `/kb-add-url https://docs.python.org/3/library/asyncio.html`

### /kb-add-local <path>
Add a local file or directory to the knowledge base.

**Usage:**
- `/kb-add-local /absolute/path/to/project`
- `/kb-add-local ./notes`

**Examples:**
- `/kb-add-local /Users/zhiqli/Documents/engineering-notes`
- `/kb-add-local ./docs`

### /kb-add-site <site-url>
Add an entire website (via sitemap) to the knowledge base.

**Usage:**
- `/kb-add-site <base-url>` - Website base URL

**Example:**
- `/kb-add-site https://fastapi.tiangolo.com`

### /kb-search <query>
Search the knowledge base for relevant information.

**Usage:**
- `/kb-search <natural language query>`

**Examples:**
- `/kb-search How to use async/await in Python?`
- `/kb-search FastAPI dependency injection examples`

### /kb-list [source-type]
List all sources in the knowledge base.

**Usage:**
- `/kb-list` - List all sources
- `/kb-list github` - List only GitHub repositories
- `/kb-list web` - List only web sources

### /kb-delete <source-id>
Delete a source from the knowledge base.

**Usage:**
- `/kb-delete <source-id>` - Source ID from /kb-list

**Example:**
- `/kb-delete github:anthropics/anthropic-sdk-python`

### /kb-status
Show knowledge base statistics and indexing status.

**Usage:**
- `/kb-status`

**Output:**
- Total sources
- Total documents indexed
- Indexing queue status
- Storage location
- Embedding model info

## Architecture

This skill interfaces with the Knowledge Base MCP Server which provides:

1. **Source Adapters**: Local filesystem, GitHub, single page, website sitemap
2. **Content Extraction**: Markdown/code from repos, trafilatura for web pages
3. **Chunking**: Header-aware markdown chunking, sliding window for plain text
4. **Embeddings**: Ollama (nomic-embed-text) for local vector generation
5. **Storage**: Chroma vector database + SQLite metadata
6. **Retrieval**: Semantic search with configurable result count

## Configuration

The MCP server is configured via environment variables or config file:

```bash
# ~/.kb/config.json
{
  "storage": {
    "persist_directory": "~/.local/share/knowledge-base",
    "collection_name": "knowledge_base"
  },
  "embeddings": {
    "provider": "ollama",
    "model": "nomic-embed-text",
    "base_url": "http://localhost:11434"
  },
  "chunking": {
    "chunk_size": 1000,
    "chunk_overlap": 200
  },
  "github": {
    "token": null,
    "max_file_size_mb": 5
  },
  "web": {
    "timeout": 30.0,
    "max_pages_per_site": 100
  }
}
```

## Requirements

- **Ollama**: Must be running locally with nomic-embed-text model
  ```bash
  ollama pull nomic-embed-text
  ollama serve
  ```

- **Python 3.10+**: Required for async features

## Installation

The skill is automatically available when the MCP server is configured in Claude Code's MCP settings.
