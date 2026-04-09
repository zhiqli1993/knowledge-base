# Knowledge Base Plugin for Claude Code

A personal knowledge base system that indexes and searches GitHub repositories, documentation sites, and web pages using semantic search.

## Features

- **GitHub Repository Indexing** - Clone and index public repos (no token required!)
- **Web Page Indexing** - Index single pages or entire websites via sitemap
- **Semantic Search** - Natural language search across all indexed content
- **Vector Database** - ChromaDB for fast similarity search
- **Local Embeddings** - Uses Ollama's nomic-embed-text (768-dim vectors)
- **No Rate Limits** - No GitHub API, no rate limits

## Installation

### Prerequisites

1. **Ollama** with `nomic-embed-text` model:
   ```bash
   # Install Ollama
   curl -fsSL https://ollama.com/install.sh | sh

   # Pull the embedding model
   ollama pull nomic-embed-text

   # Start Ollama service
   ollama serve
   ```

2. **Python 3.10+** with required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. **Git** for cloning repositories

### Install Plugin

```bash
# Install via Claude Code CLI (coming soon)
claude plugins install knowledge-base

# Or install manually
cd ~/.claude/plugins/cache
git clone https://github.com/zhiqli/knowledge-base knowledge-base-plugin
```

## Usage

Once installed, the skill is automatically available. Just use natural language:

### Add Content

```
"Add anthropics/anthropic-quickstarts to my knowledge base"
"Index the FastAPI documentation"
"Add the entire Next.js docs site to my kb"
```

### Search

```
"Search my docs for async/await examples in Python"
"Find information about Claude API customer support"
"What's in my knowledge base about FastAPI?"
```

### Manage

```
"What's in my knowledge base?"
"Show me all GitHub repos I've indexed"
"Remove the FastAPI repo from my knowledge base"
```

## How It Works

### Architecture

```
User Query → Claude Code → Knowledge Base Skill → MCP Server → Tools
                                                        ↓
                                    ┌──────────────────────────────┐
                                    │  GitHub Repos (git clone)    │
                                    │  Web Pages (trafilatura)     │
                                    └──────────────────────────────┘
                                                ↓
                                        Text Chunking
                                      (1000 chars, 200 overlap)
                                                ↓
                                    Embeddings (nomic-embed-text)
                                                ↓
                                        Vector Database
                                    ┌──────────────────────────┐
                                    │  ChromaDB (vectors)      │
                                    │  SQLite (metadata)       │
                                    └──────────────────────────┘
```

### MCP Server

The plugin uses an MCP (Model Context Protocol) server that provides these tools:

- `kb_add_repo` - Add GitHub repository
- `kb_add_url` - Add single web page
- `kb_add_site` - Add entire website
- `kb_search` - Semantic search
- `kb_list` - List all sources
- `kb_status` - Show statistics
- `kb_delete` - Remove source

### Configuration

Config file: `~/.kb/config.json`

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
  "indexing": {
    "chunk_size": 1000,
    "chunk_overlap": 200
  },
  "github": {
    "max_file_size_mb": 5
  },
  "web": {
    "timeout": 30,
    "max_pages_per_site": 100,
    "user_agent": "KnowledgeBase/1.0"
  }
}
```

## Examples

### Example 1: Python Learning Knowledge Base

```
1. "Add docs.python.org/3/library/asyncio.html to my kb"
2. "Add encode/httpx repo to my knowledge base"
3. "Search for async context manager examples"
```

### Example 2: Claude API Documentation

```
1. "Add anthropics/anthropic-quickstarts repo"
2. "Add the Anthropic documentation site"
3. "Search for best practices for prompt engineering"
```

### Example 3: Project Documentation

```
1. "Add myorg/backend-api repo"
2. "Add myorg/frontend-app repo"
3. "Search for authentication flow documentation"
```

## Performance

- **Indexing Speed**: ~5-30 seconds per repo (depending on size)
- **Search Speed**: <1 second
- **Embedding Dimensions**: 768
- **Max Repo Size**: 500 files (configurable with include/exclude patterns)

## Troubleshooting

### "Repository too large" Error

Use include/exclude patterns:
```
"Add owner/repo but only include Python files and docs"
```

The skill will automatically add patterns like:
```python
include = ["**/*.py", "**/*.md", "docs/**"]
exclude = ["**/test/**", "**/node_modules/**"]
```

### Ollama Not Running

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if needed
ollama serve
```

### Low Search Scores

Search scores of 0.003-0.015 are normal. The ranking matters, not absolute scores.

## CLI Tool

You can also use the CLI directly:

```bash
# Check status
kb status

# Add repo
kb add-repo owner/repo

# Search
kb search "your query"

# List sources
kb list
```

## Development

### Project Structure

```
knowledge-base-plugin/
├── .claude-plugin/
│   └── plugin.json          # Plugin metadata
├── skills/
│   └── knowledge-base/
│       ├── SKILL.md         # Skill definition
│       └── evals/           # Test cases
├── src/kb/          # Python package
│   ├── mcp/server.py # MCP server entrypoint
│   └── cli/main.py   # CLI tool
├── README.md
└── pyproject.toml
```

### Running Tests

```bash
# End-to-end test
python tests/e2e/test_kb_e2e.py

# Run skill evals
cd skills/knowledge-base/evals
# Test cases in evals.json
```

## License

MIT

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Run tests
4. Submit a pull request

## Credits

- Built for [Claude Code](https://claude.ai/code)
- Uses [ChromaDB](https://www.trychroma.com/) for vector storage
- Uses [Ollama](https://ollama.com/) for local embeddings
- Uses [trafilatura](https://github.com/adbar/trafilatura) for web extraction

## Support

For issues and questions:
- GitHub Issues: https://github.com/zhiqli/knowledge-base/issues
- Documentation: [USAGE.md](USAGE.md)
