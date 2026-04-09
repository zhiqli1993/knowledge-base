# Knowledge Base Claude Code Plugin

## Overview

This is a complete Claude Code plugin that provides personal knowledge base functionality with semantic search capabilities.

## What is this?

A plugin that allows Claude Code to:
- Index GitHub repositories (no token required!)
- Index web pages and entire websites
- Search all indexed content using natural language
- Manage your personal knowledge base

## Plugin Structure

```
knowledge-base-plugin/
├── .claude-plugin/
│   └── plugin.json              # Plugin metadata
├── skills/
│   └── knowledge-base/
│       ├── SKILL.md             # Skill definition (auto-loaded by Claude)
│       └── evals/
│           └── evals.json       # Test cases
├── src/kb/              # Python package (symlink)
│   ├── mcp/server.py    # MCP server entrypoint
│   └── cli/main.py      # CLI tool
├── install.sh                   # Automated installer
├── README.md                    # Full documentation
├── QUICKSTART.md                # 5-minute getting started guide
├── USAGE.md                     # Detailed usage guide
├── docs/test-results.md              # Test results and examples
└── LICENSE                      # MIT License
```

## Installation Methods

### Method 1: Automated Installer (Recommended)

```bash
cd /Users/zhiqli/knowledge-base/knowledge-base-plugin
./install.sh
```

This will:
- Check all prerequisites
- Install dependencies
- Setup configuration
- Install the skill
- Give you next steps

### Method 2: Manual Installation

```bash
# 1. Install dependencies
pip3 install -r requirements.txt

# 2. Pull Ollama model
ollama pull nomic-embed-text

# 3. Copy skill
cp -r skills/knowledge-base ~/.claude/skills/

# 4. Create config
mkdir -p ~/.kb
# ... (see install.sh for config template)

# 5. Restart Claude Code
```

## How It Works

### Architecture

```
User → Claude Code → Knowledge Base Skill → MCP Server
                           ↓
                   ┌──────────────────┐
                   │  Content Sources │
                   │  - GitHub Repos  │
                   │  - Web Pages     │
                   │  - Websites      │
                   └──────────────────┘
                           ↓
                   Text Chunking (1000 chars)
                           ↓
                   Embeddings (nomic-embed-text)
                           ↓
                   ┌──────────────────┐
                   │  Vector Database │
                   │  - ChromaDB      │
                   │  - SQLite        │
                   └──────────────────┘
```

### Components

1. **Skill** (`skills/knowledge-base/SKILL.md`)
   - Loaded automatically by Claude Code
   - Triggers on natural language about knowledge base
   - Provides instructions for using MCP tools

2. **MCP Server** (`src/kb/`)
   - Provides 7 MCP tools
   - Handles indexing and searching
   - Manages vector database

3. **CLI Tool** (`kb` / `src/kb/cli/main.py`)
   - Direct command-line access
   - Useful for testing and debugging

## MCP Tools Provided

The plugin adds these tools to Claude Code:

| Tool | Description |
|------|-------------|
| `kb_add_repo` | Add GitHub repository |
| `kb_add_url` | Add single web page |
| `kb_add_site` | Add entire website |
| `kb_search` | Semantic search |
| `kb_list` | List all sources |
| `kb_status` | Show statistics |
| `kb_delete` | Remove source |

## Usage Examples

### Natural Language (via Skill)

```
User: "Add the FastAPI repo to my knowledge base"
→ Skill triggers → Calls kb_add_repo

User: "Search for async examples"
→ Skill triggers → Calls kb_search

User: "What's in my knowledge base?"
→ Skill triggers → Calls kb_status
```

### Direct MCP Tool Usage

Claude can also call the tools directly:
```
mcp__knowledge-base__kb_search(query="async examples", n_results=5)
```

### CLI Usage

```bash
kb status
kb add-repo owner/repo
kb search "your query"
```

## Requirements

- **Python 3.10+**
- **Ollama** with `nomic-embed-text` model
- **Git**
- **Claude Code** with MCP support

## Configuration

Config file: `~/.kb/config.json`

Key settings:
- `chroma.persist_directory` - Where to store data
- `ollama.model` - Embedding model (nomic-embed-text)
- `indexing.chunk_size` - Text chunk size (1000)
- `github.max_file_size_mb` - Max file size (5MB)

## Testing

### Automated Tests

```bash
# End-to-end test
python3 tests/e2e/test_kb_e2e.py

# Skill evaluation tests
cd skills/knowledge-base/evals
# See evals.json for test cases
```

### Test Results

See `docs/test-results.md` for:
- ✅ All tests passed (100% pass rate)
- Performance metrics
- Example outputs

## Performance

- **Indexing**: 5-30 seconds per repo
- **Search**: <1 second
- **Embeddings**: 768 dimensions
- **Max repo size**: 500 files

## Limitations

1. **GitHub**: 500 files max per repo (use include/exclude patterns for larger repos)
2. **Web**: 100 pages max per site (configurable)
3. **Local only**: Requires Ollama running locally
4. **Public repos**: No private GitHub repo support (by design - no tokens)

## Troubleshooting

See QUICKSTART.md and README.md for detailed troubleshooting.

Quick fixes:
- Ollama not running: `ollama serve`
- Model missing: `ollama pull nomic-embed-text`
- Skill not loading: Restart Claude Code

## Development

### Project Structure

The plugin is part of a larger project:

```
knowledge-base/
├── knowledge-base-plugin/     # This plugin
├── src/kb/                    # Python package
│   ├── mcp/server.py          # MCP server entrypoint
│   └── cli/main.py            # CLI implementation
├── tests/e2e/test_kb_e2e.py            # Tests
├── .mcp.json                  # MCP config for project
└── pyproject.toml             # Dependencies and packaging
```

The plugin uses symlinks to the actual code, making it easy to develop and test.

### Making Changes

1. Edit files in the main project directory
2. Changes are immediately reflected in the plugin (via symlinks)
3. Test with `python3 tests/e2e/test_kb_e2e.py`
4. Update version in `.claude-plugin/plugin.json`
5. Commit and tag

## Distribution

### GitHub Release

1. Tag version: `git tag v1.0.0`
2. Push: `git push origin v1.0.0`
3. Create GitHub release
4. Users can install with:
   ```bash
   git clone https://github.com/zhiqli/knowledge-base.git
   cd knowledge-base/knowledge-base-plugin
   ./install.sh
   ```

### Claude Code Plugin Marketplace (Future)

When available, this plugin can be published to the official marketplace.

## License

MIT - See LICENSE file

## Credits

- Built with [Claude Code](https://claude.ai/code)
- Uses [ChromaDB](https://www.trychroma.com/)
- Uses [Ollama](https://ollama.com/)
- Uses [trafilatura](https://github.com/adbar/trafilatura)

## Support

- **GitHub**: https://github.com/zhiqli/knowledge-base
- **Issues**: https://github.com/zhiqli/knowledge-base/issues
- **Docs**: README.md, USAGE.md, QUICKSTART.md
