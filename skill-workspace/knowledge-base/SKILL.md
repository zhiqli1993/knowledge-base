---
name: knowledge-base
description: Manage a personal knowledge base for indexing and searching GitHub repositories, documentation, and web pages. Use this skill whenever the user mentions knowledge base, wants to index code/docs, search their indexed content, or asks about adding repositories or websites to their knowledge system. Also trigger when user says things like "add this repo to kb", "search my docs for X", "index this website", or "what's in my knowledge base".
---

# Knowledge Base Skill

This skill helps you manage a personal knowledge base system that indexes GitHub repositories, documentation sites, and web pages into a searchable vector database.

## When to Use This Skill

Invoke this skill when the user wants to:
- **Add content**: Index GitHub repos, web pages, or entire websites
- **Search**: Find information across their indexed content
- **Manage**: View what's indexed, check status, or remove sources
- **Ask about**: Their knowledge base system or what's available

Common trigger phrases:
- "Add [repo/url] to my knowledge base"
- "Search my docs for [query]"
- "What's in my knowledge base?"
- "Index this repository"
- "Search for [topic] in my indexed content"

## Available Operations

### 1. Add GitHub Repository

Add a public GitHub repository (no token needed).

**When to use**: User provides a GitHub repo URL or owner/repo format and wants to index it.

**Tool**: `mcp__knowledge-base__kb_add_repo`

**Parameters**:
- `repo_url`: GitHub repo in format "owner/repo" or full URL
- `branch`: Branch to index (default: "main")
- `include`: Optional file patterns to include
- `exclude`: Optional file patterns to exclude

**Example invocation**:
```
User: "Add anthropics/anthropic-sdk-python to my knowledge base"

→ Call mcp__knowledge-base__kb_add_repo with:
  - repo_url: "anthropics/anthropic-sdk-python"
  - branch: "main"
```

**What happens**: Repository is cloned using git and indexed in the background. Files matching include/exclude patterns are chunked, embedded, and stored.

**Important notes**:
- Maximum 500 files per repo (limit prevents overwhelming the system)
- If repo is too large, suggest using more specific include/exclude patterns
- No GitHub token needed for public repos
- Indexing happens in background - other operations won't be blocked

### 2. Add Web Page

Add a single web page to the knowledge base.

**When to use**: User provides a URL and wants to index that specific page.

**Tool**: `mcp__knowledge-base__kb_add_url`

**Parameters**:
- `url`: Web page URL

**Example invocation**:
```
User: "Index the FastAPI documentation homepage"

→ Call mcp__knowledge-base__kb_add_url with:
  - url: "https://fastapi.tiangolo.com/"
```

### 3. Add Website

Add an entire website via sitemap (indexes multiple pages).

**When to use**: User wants to index a whole documentation site or multiple pages.

**Tool**: `mcp__knowledge-base__kb_add_site`

**Parameters**:
- `base_url`: Website base URL
- `max_pages`: Optional maximum pages to index

**Example invocation**:
```
User: "Index the entire FastAPI documentation site"

→ Call mcp__knowledge-base__kb_add_site with:
  - base_url: "https://fastapi.tiangolo.com"
  - max_pages: 100
```

### 4. Search Knowledge Base

Search across all indexed content using semantic search.

**When to use**: User asks a question or wants to find information in their indexed content.

**Tool**: `mcp__knowledge-base__kb_search`

**Parameters**:
- `query`: Natural language search query
- `n_results`: Number of results (default: 5)
- `source_filter`: Optional filter by source type ("github", "web_page", "web_site")

**Example invocation**:
```
User: "Search for async/await examples in Python"

→ Call mcp__knowledge-base__kb_search with:
  - query: "async await Python examples"
  - n_results: 5
```

**Output format**: Returns ranked results with:
- Source (repo or URL)
- File path
- Relevance score
- Text snippet

### 5. View Knowledge Base Status

Show statistics about the knowledge base.

**When to use**: User asks "what's in my knowledge base", "kb status", or wants to see statistics.

**Tool**: `mcp__knowledge-base__kb_status`

**No parameters needed**.

**Example invocation**:
```
User: "What's in my knowledge base?"

→ Call mcp__knowledge-base__kb_status
```

**Output includes**:
- Total sources
- Indexed/indexing/pending/failed counts
- Total documents and chunks
- Storage location
- Embedding model info

### 6. List Sources

List all indexed sources with their status.

**When to use**: User wants to see what's indexed, check indexing status, or browse sources.

**Tool**: `mcp__knowledge-base__kb_list`

**Parameters**:
- `source_type`: Optional filter ("github", "web_page", "web_site")

**Example invocation**:
```
User: "Show me all GitHub repos in my knowledge base"

→ Call mcp__knowledge-base__kb_list with:
  - source_type: "github"
```

**Output includes**: For each source:
- Source ID
- Type (github_repo, web_page, web_site)
- URL
- Status (ready, indexing, pending, error)
- Error message (if failed)
- Last indexed time (if completed)

### 7. Delete Source

Remove a source from the knowledge base.

**When to use**: User wants to remove indexed content.

**Tool**: `mcp__knowledge-base__kb_delete`

**Parameters**:
- `source_id`: Source identifier (from kb_list)

**Example invocation**:
```
User: "Remove the FastAPI repo from my knowledge base"

→ First call kb_list to find the source_id
→ Then call mcp__knowledge-base__kb_delete with:
  - source_id: "github:tiangolo/fastapi"
```

**Important**: Always confirm the source_id before deleting. Show the user what will be deleted.

## Understanding the Output

### Search Results
- **Score**: Relevance score (higher = more relevant, typically 0.003-0.015)
- **Source**: Where the content came from
- **File**: Specific file path
- **Text**: Relevant snippet

### Error Messages
The system provides helpful error messages:
- **"Repository too large"**: Repo has >500 files, suggest using include/exclude patterns
- **"Redirect"**: URL redirected, suggests the new URL to use
- **"Failed to fetch"**: Network or access issue with the URL

## How It Works (Background Info)

Understanding the system helps you use it effectively:

1. **Indexing Pipeline**:
   - GitHub repos: Cloned with `git clone --depth 1` (fast, no history)
   - Web pages: Fetched and extracted with trafilatura
   - Content: Chunked into 1000-char pieces with 200-char overlap
   - Embeddings: Generated using Ollama's nomic-embed-text (768-dim vectors)
   - Storage: ChromaDB for vectors + SQLite for metadata

2. **Search**:
   - Converts query to embedding
   - Finds most similar chunks in vector database
   - Returns ranked results with context

3. **No Token Required**:
   - Public repos cloned directly (no GitHub API)
   - No rate limits
   - Works offline after initial setup

## Best Practices

### For Adding Repos
- Start with smaller repos (<100 files) to test
- Use include/exclude patterns for large repos:
  - Include: `["**/*.md", "**/*.py", "docs/**"]`
  - Exclude: `["**/node_modules/**", "**/test/**"]`
- Check status after adding to see if indexing succeeded

### For Searching
- Use natural language queries (not just keywords)
- Good: "How to handle async errors in Python"
- Less good: "async error"
- Adjust `n_results` based on need (3-10 usually sufficient)

### For Managing
- Run `kb_status` periodically to check for failed indexing
- Failed sources show error messages - read them for guidance
- Remove unused sources to keep the database lean

## Example Workflows

### Workflow 1: Building a Python Learning Knowledge Base
```
User: "I want to learn async Python, help me build a knowledge base"

1. Add Python docs:
   → kb_add_url: https://docs.python.org/3/library/asyncio.html

2. Add example repos:
   → kb_add_repo: "encode/httpx" (async HTTP)
   → kb_add_repo: "tiangolo/fastapi" (async web framework)

3. Search for specific topics:
   → kb_search: "async context managers Python"
   → kb_search: "asyncio best practices"

4. Check what's indexed:
   → kb_status
```

### Workflow 2: Research Assistant
```
User: "I'm researching Claude AI capabilities"

1. Add official docs:
   → kb_add_site: "https://docs.anthropic.com"

2. Add example repos:
   → kb_add_repo: "anthropics/anthropic-quickstarts"

3. Search across everything:
   → kb_search: "Claude API function calling"
   → kb_search: "prompt engineering best practices"
```

### Workflow 3: Project Documentation
```
User: "Index my team's internal documentation"

1. Add repos:
   → kb_add_repo: "myorg/backend-api"
   → kb_add_repo: "myorg/frontend-app"

2. Add wiki/docs:
   → kb_add_url: "https://wiki.company.com/api-guide"

3. Search when needed:
   → kb_search: "authentication flow"
   → kb_search: "deployment process"
```

## Troubleshooting

### "Repository too large" Error
**Solution**: Use include/exclude patterns to limit files:
```
kb_add_repo with:
  - include: ["**/*.md", "**/*.py", "src/**"]
  - exclude: ["**/test/**", "**/node_modules/**"]
```

### "Redirect" or "Failed to fetch" for URLs
**Solution**:
- Try the redirect URL provided in error message
- Check if URL requires authentication
- Verify URL is accessible

### Low Search Scores
This is normal - scores of 0.003-0.015 are typical. The ranking is what matters, not the absolute score.

### Indexing Takes Long
- GitHub repos: ~5-30 seconds depending on size
- Web pages: ~5-10 seconds
- Large websites: Can take several minutes
- Check `kb_status` to see progress

## System Requirements

The MCP server requires:
- **Ollama** running locally with `nomic-embed-text` model
- **Python 3.10+**
- **Git** (for cloning repos)

If these aren't set up, the tools will return errors with guidance.
