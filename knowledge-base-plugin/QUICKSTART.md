# Knowledge Base Plugin - Quick Start

## 1. Install

```bash
cd /Users/zhiqli/knowledge-base
pip install -e .
```

## 2. Start dependencies

```bash
ollama serve
kb serve
```

## 3. Configure Claude Code

Ensure `.mcp.json` points to:

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

## 4. Try it

Examples in Claude Code:

- “Add anthropics/anthropic-quickstarts to my knowledge base”
- “Add ./docs to my kb”
- “Search my docs for async examples”
- “Show progress for the last source”

## 5. Manual verification

```bash
kb status
kb add-repo anthropics/anthropic-quickstarts
kb search "async python"
kb list
```

## Troubleshooting

- Service not responding → `kb serve`
- MCP not loading → restart Claude Code
- Package missing → `pip install -e .`
- Ollama missing → `ollama pull nomic-embed-text`
