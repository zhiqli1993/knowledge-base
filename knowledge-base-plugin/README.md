# Knowledge Base Plugin for Claude Code

This plugin exposes the project's MCP integration to Claude Code.

The project itself now uses a **service-oriented architecture**:

- `kb` CLI → HTTP client → KB Web Service
- `kb.mcp.server` → HTTP client → KB Web Service

## What the plugin gives you

- MCP tools for indexing and searching
- Access to local file, GitHub, URL, and site sources
- Shared status and progress reporting
- Alignment with the same backend used by the CLI

## Requirements

1. Python 3.10+
2. Ollama with `nomic-embed-text`
3. Installed package:

```bash
cd /Users/zhiqli/knowledge-base
pip install -e .
```

4. Local KB service running:

```bash
kb serve
```

## MCP Tools

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

## Claude Code MCP Config

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

## Project Structure

```text
knowledge-base/
├── src/kb/
│   ├── cli/
│   ├── client/
│   ├── core/
│   ├── http/
│   ├── mcp/
│   ├── service/
│   └── sources/
├── knowledge-base-plugin/
├── docs/
└── tests/
```

## Validate

```bash
kb status
pytest -q
```

## Related Docs

- `QUICKSTART.md` for a minimal setup flow
- `LANGUAGE_DETECTION.md` for GitHub repo indexing exclude behavior
