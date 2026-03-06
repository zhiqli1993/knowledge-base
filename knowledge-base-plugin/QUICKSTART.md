# Knowledge Base Plugin - Quick Start

Get up and running in 5 minutes!

## Install

```bash
# Clone the plugin
git clone https://github.com/zhiqli/knowledge-base.git
cd knowledge-base/knowledge-base-plugin

# Run installer
./install.sh
```

The installer will:
- ✅ Check prerequisites (Python, Ollama, Git)
- ✅ Install Python dependencies
- ✅ Pull nomic-embed-text model
- ✅ Create config files
- ✅ Install the skill

## Quick Test

### 1. Start Ollama (if not running)

```bash
ollama serve
```

### 2. Restart Claude Code

Quit and reopen Claude Code to load the new skill.

### 3. Try it!

In Claude Code, say:

```
"Add anthropics/anthropic-quickstarts to my knowledge base"
```

Wait ~30 seconds for indexing, then search:

```
"Search my docs for customer support examples"
```

## Common Commands

### Add Content

```
"Add fastapi/fastapi to my kb"
"Index https://fastapi.tiangolo.com/"
"Add the entire Next.js documentation site"
```

### Search

```
"Search for async/await Python examples"
"Find Claude API authentication docs"
"What do I have about FastAPI?"
```

### Manage

```
"What's in my knowledge base?"
"Show all repos I've indexed"
"List web pages in my kb"
```

## Manual Testing (without Claude Code)

Use the CLI tool:

```bash
# Check status
python3 kb_cli.py status

# Add a repo
python3 kb_cli.py add-repo anthropics/anthropic-quickstarts main

# Search
python3 kb_cli.py search "async python"

# List all sources
python3 kb_cli.py list
```

## Troubleshooting

### Ollama not running

```bash
# Check
curl http://localhost:11434/api/tags

# Start if needed
ollama serve
```

### Model not installed

```bash
ollama pull nomic-embed-text
```

### Skill not loading in Claude Code

1. Check skill is installed:
   ```bash
   ls ~/.claude/skills/knowledge-base/
   ```

2. Restart Claude Code completely

3. Check Claude Code logs for errors

### MCP Server not responding

1. Check .mcp.json exists:
   ```bash
   cat /Users/zhiqli/knowledge-base/.mcp.json
   ```

2. Verify PYTHONPATH is correct

3. Restart Claude Code

## What's Next?

- Read [USAGE.md](USAGE.md) for detailed features
- Check [TEST_RESULTS.md](TEST_RESULTS.md) for examples
- Run tests: `python3 test_kb_e2e.py`

## Getting Help

- **Issues**: https://github.com/zhiqli/knowledge-base/issues
- **Docs**: See README.md and USAGE.md
- **Examples**: See TEST_RESULTS.md

## Uninstall

```bash
# Remove skill
rm -rf ~/.claude/skills/knowledge-base

# Remove data (optional)
rm -rf ~/.local/share/knowledge-base

# Remove config (optional)
rm -rf ~/.config/knowledge-base
```
