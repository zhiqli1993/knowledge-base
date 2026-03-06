# Knowledge Base System

Personal knowledge base that extracts knowledge from GitHub repos, documentation sites, and web pages, stores them in Chroma vector database, and integrates with Claude Code via MCP Server + Skill.

## Features

- Extract knowledge from GitHub repositories
- Extract knowledge from web pages and documentation sites
- Store in Chroma vector database with Ollama embeddings
- MCP Server for persistent storage
- Skill commands for convenient use
- Auto context enhancement via MCP Resources

## Installation

See docs/plans/2026-03-06-knowledge-base-design.md for full setup instructions.

## Development

```bash
cd mcp-server
pip install -r requirements.txt
pytest
```