# Knowledge Base System Design

**Date:** 2026-03-06
**Status:** Approved
**Type:** MCP Server + Skill Integration

## Overview

A personal knowledge base system that extracts knowledge from GitHub repositories, documentation sites, and web pages, stores them in a vector database (Chroma), and provides seamless integration with Claude Code through MCP protocol and Skill commands.

## Requirements Summary

- **Knowledge Sources**: GitHub repos, web pages, documentation sites, local files
- **Vector Database**: Chroma (via Python SDK)
- **Embedding Model**: Ollama (nomic-embed-text)
- **Deployment**: MCP Server (persistent) + Skill (convenient commands)
- **Usage Mode**: Hybrid (auto context enhancement + manual search)
- **Extraction Strategy**: Smart hybrid (docs + key code) + configurable

## Architecture

### System Components

```
knowledge-base/
├── mcp-server/              # MCP Server (Python)
│   ├── server.py           # MCP protocol entry point
│   ├── indexer.py          # Indexing service (GitHub/Web → Chroma)
│   ├── retriever.py        # Retrieval service (query Chroma)
│   ├── sources/            # Data source adapters
│   │   ├── github.py       # GitHub API integration
│   │   ├── web.py          # Web scraper
│   │   └── local.py        # Local files
│   ├── models.py           # Data models
│   ├── storage.py          # Metadata storage (SQLite)
│   └── config.py           # Configuration management
├── skill/                   # Claude Code Skill
│   └── SKILL.md            # Skill definition
└── docs/
    └── plans/              # Design documents
```

### Technology Stack

- **MCP Server**: Python 3.11+, FastMCP framework
- **Vector Database**: Chroma (via Python SDK)
- **Embedding**: Ollama (nomic-embed-text or mxbai-embed-large)
- **Metadata Storage**: SQLite (track sources, update times)
- **GitHub API**: PyGithub
- **Web Scraping**: trafilatura + requests

### Architecture Pattern: Independent Service Mode

```
Skill → Knowledge Base MCP Server
           ├─ Chroma Python SDK (direct call)
           ├─ Ollama HTTP API
           ├─ GitHub API / Web Scraper
           └─ Local Cache (SQLite)
```

**Why this approach:**
- Single-layer MCP call, optimal performance
- Full control for optimization (batching, caching, rate limiting)
- Independent metadata storage (SQLite) for advanced queries
- Support for incremental updates

### Data Flow

**1. Adding Knowledge Source:**
```
Skill Command → MCP Tool → Indexer
                              ↓
                    GitHub/Web → Parse → Chunk → Embed → Chroma
                                                         ↓
                                                      SQLite (metadata)
```

**2. Querying Knowledge:**
```
User Question → MCP Resource → Retriever → Chroma Search
                                              ↓
                                           Format Results → Claude
```

## Data Model

### Chroma Collection Structure

**Collection**: `knowledge_base`

**Document Structure**:
```python
{
  "id": "github:owner/repo:path/to/file.md:chunk_0",
  "document": "actual text content of the chunk...",
  "embedding": [0.123, 0.456, ...],  # auto-generated
  "metadata": {
    "source_type": "github|web|local",
    "source_id": "source_uuid",
    "file_path": "src/index.ts",
    "chunk_index": 0,
    "language": "typescript",
    "url": "https://github.com/owner/repo/blob/main/src/index.ts",
    "title": "File or page title",
    "indexed_at": "2026-03-06T17:00:00Z"
  }
}
```

### SQLite Metadata Schema

```sql
-- Knowledge sources table
CREATE TABLE sources (
  id TEXT PRIMARY KEY,              -- UUID
  type TEXT NOT NULL,               -- 'github_repo', 'github_file', 'web_page', 'web_site', 'local'
  url TEXT NOT NULL,                -- Source URL
  name TEXT,                        -- Display name
  config JSON,                      -- Extraction config (glob patterns, exclude rules)
  status TEXT DEFAULT 'pending',    -- 'pending', 'indexing', 'ready', 'error'
  error_message TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_indexed_at TIMESTAMP,
  document_count INTEGER DEFAULT 0,
  chunk_count INTEGER DEFAULT 0
);

-- Documents table (track each file/page)
CREATE TABLE documents (
  id TEXT PRIMARY KEY,              -- UUID
  source_id TEXT NOT NULL,
  file_path TEXT,                   -- File path or URL
  content_hash TEXT,                -- SHA256, for change detection
  chunk_count INTEGER,
  indexed_at TIMESTAMP,
  FOREIGN KEY (source_id) REFERENCES sources(id)
);

-- Index queue (support async indexing)
CREATE TABLE index_queue (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_id TEXT NOT NULL,
  priority INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (source_id) REFERENCES sources(id)
);
```

### Chunking Strategy

**Smart Chunking Logic**:
- **Markdown**: Split by header hierarchy (preserve semantic integrity)
- **Code**: Split by function/class boundaries
- **Plain text**: Sliding window (chunk_size=1000, overlap=200)

**Example**:
```python
def chunk_markdown(content: str, max_size: int = 1000) -> List[str]:
    """
    Chunk by header hierarchy, maintain context integrity
    Priority: # > ## > ### > paragraph
    Each chunk includes header breadcrumb
    """
    pass
```

## Interface Design

### MCP Tools (called by Skill)

```python
# 1. Add GitHub repository
@mcp.tool()
def add_github_repo(
    repo_url: str,           # "https://github.com/owner/repo" or "owner/repo"
    branch: str = "main",
    include: List[str] = None,  # ["**/*.md", "src/**/*.ts"]
    exclude: List[str] = None   # ["tests/**", "*.test.ts"]
) -> dict:
    """Add a GitHub repository to knowledge base"""

# 2. Add single URL
@mcp.tool()
def add_web_page(
    url: str,
    title: str = None  # Optional custom title
) -> dict:
    """Add a single web page to knowledge base"""

# 3. Add entire documentation site
@mcp.tool()
def add_web_site(
    url: str,
    max_pages: int = 100  # Prevent over-crawling
) -> dict:
    """Add entire documentation site via sitemap"""

# 4. Manually search knowledge base
@mcp.tool()
def search_knowledge(
    query: str,
    top_k: int = 5,
    filter: dict = None  # {"source_type": "github", "language": "python"}
) -> dict:
    """Search knowledge base manually"""

# 5. List all knowledge sources
@mcp.tool()
def list_sources(
    source_type: str = None  # Optional filter
) -> List[dict]:
    """List all knowledge sources"""

# 6. Delete knowledge source
@mcp.tool()
def delete_source(
    source_id: str,
    delete_chunks: bool = True  # Whether to delete chunks in Chroma
) -> dict:
    """Delete a knowledge source"""

# 7. Re-index knowledge source
@mcp.tool()
def reindex_source(
    source_id: str
) -> dict:
    """Re-index a knowledge source (detect changes)"""
```

### MCP Resources (auto context enhancement)

```python
# Dynamically generate Resource, auto-retrieve based on user conversation context
@mcp.resource("knowledge://search/{query}")
def get_relevant_knowledge(query: str) -> str:
    """
    Auto-invoked when Claude determines knowledge base support is needed
    Returns relevant document snippets in Markdown format
    """
    results = retriever.search(query, top_k=3)
    return format_results_as_markdown(results)
```

### Skill Command Interface

**Commands defined in SKILL.md:**

- `/kb-add-repo <repo_url>` - Add GitHub repository
- `/kb-add-url <url>` - Add single web page
- `/kb-add-site <url>` - Add entire documentation site
- `/kb-search <query>` - Search knowledge base
- `/kb-list [type]` - List all knowledge sources
- `/kb-delete <source_id>` - Delete knowledge source
- `/kb-reindex <source_id>` - Re-index knowledge source
- `/kb-status` - View indexing status

**Example Interaction:**
```
User: /kb-add-repo vercel/next.js
Assistant: [calls mcp.add_github_repo("vercel/next.js")]
          ✅ Added Next.js repository
          📄 Indexing 234 files (docs/, examples/)
          ⏳ Estimated time: 2 minutes

User: How to configure SSR in Next.js?
Assistant: [auto-triggers knowledge://search/next.js SSR configuration]
          Based on the documentation in the knowledge base...
```

## Core Processing Flows

### Indexing Pipeline

```python
async def index_source(source_id: str):
    """
    Complete indexing flow
    """
    # 1. Get source config
    source = db.get_source(source_id)

    # 2. Select adapter by type
    if source.type == 'github_repo':
        fetcher = GitHubRepoFetcher(source.url, source.config)
    elif source.type == 'web_site':
        fetcher = WebSiteFetcher(source.url, source.config)

    # 3. Get file list
    files = await fetcher.list_files()

    # 4. Batch processing (avoid API rate limiting)
    for batch in chunked(files, batch_size=10):
        tasks = [process_file(f, source_id) for f in batch]
        await asyncio.gather(*tasks)

    # 5. Update metadata
    db.update_source_status(source_id, 'ready')

async def process_file(file_info: FileInfo, source_id: str):
    """
    Process single file
    """
    # 1. Download content
    content = await file_info.download()

    # 2. Check if already indexed (via content_hash)
    content_hash = sha256(content)
    existing_doc = db.get_document_by_hash(source_id, content_hash)
    if existing_doc:
        return  # Skip unchanged files

    # 3. Chunk
    chunks = chunker.chunk(content, file_info.file_type)

    # 4. Batch generate embeddings
    texts = [c.text for c in chunks]
    embeddings = await ollama_client.embed_batch(texts)

    # 5. Write to Chroma
    chroma_docs = [
        {
            "id": f"{source_id}:{file_info.path}:chunk_{i}",
            "document": text,
            "embedding": emb,
            "metadata": {
                "source_id": source_id,
                "file_path": file_info.path,
                "chunk_index": i,
                "language": file_info.language,
                "url": file_info.url,
                **chunks[i].metadata
            }
        }
        for i, (text, emb) in enumerate(zip(texts, embeddings))
    ]

    chroma_collection.add(
        ids=[d["id"] for d in chroma_docs],
        documents=[d["document"] for d in chroma_docs],
        embeddings=[d["embedding"] for d in chroma_docs],
        metadatas=[d["metadata"] for d in chroma_docs]
    )

    # 6. Update SQLite
    db.upsert_document(source_id, file_info.path, content_hash, len(chunks))
```

### Retrieval Pipeline

```python
def search(query: str, top_k: int = 5, filter: dict = None) -> List[SearchResult]:
    """
    Retrieve knowledge
    """
    # 1. Generate query embedding
    query_embedding = ollama_client.embed(query)

    # 2. Vector search
    where_filter = build_chroma_filter(filter) if filter else None

    results = chroma_collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where_filter,
        include=["documents", "metadatas", "distances"]
    )

    # 3. Format results
    search_results = [
        SearchResult(
            content=doc,
            metadata=meta,
            score=1 - distance,  # Convert to similarity score
            source=db.get_source(meta["source_id"])
        )
        for doc, meta, distance in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        )
    ]

    # 4. Sort by score and deduplicate (multiple chunks from same file)
    return deduplicate_and_rank(search_results)
```

### Incremental Update Flow

```python
async def reindex_source(source_id: str):
    """
    Incremental update: only process changed files
    """
    source = db.get_source(source_id)
    fetcher = get_fetcher(source)

    # Get current file list with hashes
    current_files = await fetcher.list_files_with_hash()
    existing_docs = db.get_documents_by_source(source_id)

    # Detect changes
    to_delete = []
    to_update = []
    to_add = []

    for doc in existing_docs:
        if doc.file_path not in current_files:
            to_delete.append(doc)  # File deleted
        elif current_files[doc.file_path] != doc.content_hash:
            to_update.append(doc)  # File modified

    for path, hash in current_files.items():
        if path not in {d.file_path for d in existing_docs}:
            to_add.append(path)  # New file

    # Execute updates
    await delete_chunks(to_delete)
    await process_files(to_update + to_add, source_id)
```

## Error Handling and Fault Tolerance

### Common Error Scenarios

**1. API Rate Limiting (GitHub, Web)**
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type(RateLimitError)
)
async def fetch_with_retry(url: str):
    """Request with retry"""
    try:
        response = await client.get(url)
        if response.status_code == 429:
            raise RateLimitError(f"Rate limited, retry after {response.headers.get('Retry-After')}")
        return response
    except Exception as e:
        logger.warning(f"Fetch failed: {url}, error: {e}")
        raise
```

**2. Ollama Service Unavailable**
```python
async def ensure_ollama_available():
    """Check Ollama service before startup"""
    try:
        response = await ollama_client.list_models()
        if "nomic-embed-text" not in response.models:
            logger.warning("Pulling nomic-embed-text model...")
            await ollama_client.pull("nomic-embed-text")
    except ConnectionError:
        raise RuntimeError(
            "Ollama is not running. Please start it with: ollama serve"
        )
```

**3. Chroma Connection Failure**
```python
def get_chroma_client(max_retries=3):
    """Chroma connection with retry"""
    for attempt in range(max_retries):
        try:
            client = chromadb.HttpClient(
                host=config.chroma.host,
                port=config.chroma.port
            )
            client.heartbeat()  # Test connection
            return client
        except Exception as e:
            if attempt == max_retries - 1:
                raise RuntimeError(
                    f"Cannot connect to Chroma at {config.chroma.host}:{config.chroma.port}\n"
                    f"Please ensure Chroma is running."
                )
            time.sleep(2 ** attempt)
```

**4. Resume Interrupted Indexing**
```python
async def resume_interrupted_indexing():
    """Resume interrupted indexing tasks on startup"""
    interrupted = db.get_sources_by_status('indexing')
    for source in interrupted:
        logger.info(f"Resuming indexing for {source.name}")
        # Reset status and re-index
        db.update_source_status(source.id, 'pending')
        await queue_for_indexing(source.id)
```

### Data Consistency Guarantees

**Transactional Operations**:
```python
async def add_chunks_transactional(chunks: List[Chunk], document_id: str):
    """Ensure consistency between Chroma and SQLite"""
    try:
        # 1. Write to Chroma
        chroma_collection.add(
            ids=[c.id for c in chunks],
            documents=[c.text for c in chunks],
            embeddings=[c.embedding for c in chunks],
            metadatas=[c.metadata for c in chunks]
        )

        # 2. Update SQLite
        with db.transaction():
            db.upsert_document(document_id, chunk_count=len(chunks))

    except Exception as e:
        # 3. Rollback Chroma (delete inserted chunks)
        logger.error(f"Transaction failed, rolling back: {e}")
        chroma_collection.delete(ids=[c.id for c in chunks])
        raise
```

### User Feedback Mechanism

**Progress Reporting**:
```python
# MCP Tool returns progress information
{
    "status": "indexing",
    "source_id": "uuid-123",
    "progress": {
        "total_files": 234,
        "processed_files": 45,
        "percentage": 19.2,
        "estimated_time_remaining": "3 minutes"
    },
    "message": "Indexing Next.js repository... (45/234 files)"
}
```

**Error Messages**:
```python
# User-friendly error messages
{
    "status": "error",
    "error_type": "rate_limit",
    "message": "GitHub API rate limit exceeded. Indexing paused.",
    "suggestion": "Retry will happen automatically in 15 minutes, or you can provide a GitHub token in config.",
    "retry_at": "2026-03-06T18:00:00Z"
}
```

## Deployment and Configuration

### System Dependencies

- Python 3.11+
- Ollama (requires running `ollama serve`)
- Chroma (via Python SDK or standalone service)

### Python Dependencies (`requirements.txt`)

```txt
fastmcp>=1.0.0
chromadb>=0.4.0
pygithub>=2.0.0
trafilatura>=1.6.0
httpx>=0.25.0
aiosqlite>=0.19.0
tenacity>=8.2.0
pydantic>=2.0.0
click>=8.1.0
```

### Installation and Configuration

**1. Initialization Command**:
```bash
# Auto-install script
kb-init

# Execution steps:
# 1. Create ~/.claude/knowledge-base/ directory
# 2. Generate default config file
# 3. Check if Ollama is running
# 4. Pull embedding model
# 5. Initialize Chroma collection
# 6. Create SQLite database
# 7. Configure MCP Server to ~/.claude/mcp-servers/knowledge-base/
```

**2. Configuration File** (`~/.claude/knowledge-base/config.json`):
```json
{
  "chroma": {
    "host": "localhost",
    "port": 8000,
    "collection_name": "knowledge_base",
    "persist_directory": "~/.claude/knowledge-base/chroma_db"
  },
  "ollama": {
    "host": "localhost",
    "port": 11434,
    "model": "nomic-embed-text",
    "timeout": 60
  },
  "github": {
    "token": null,
    "max_file_size_mb": 5
  },
  "web": {
    "user_agent": "KnowledgeBase/1.0",
    "timeout": 30,
    "max_pages_per_site": 100
  },
  "indexing": {
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "batch_size": 10,
    "default_includes": [
      "**/*.md",
      "**/README*",
      "**/docs/**",
      "**/*.ts",
      "**/*.py",
      "**/*.go"
    ],
    "default_excludes": [
      "**/node_modules/**",
      "**/.git/**",
      "**/dist/**",
      "**/build/**",
      "**/*.test.*",
      "**/*.spec.*"
    ]
  },
  "retrieval": {
    "default_top_k": 5,
    "similarity_threshold": 0.7
  }
}
```

**3. MCP Server Registration** (`~/.claude/settings.json`):
```json
{
  "mcpServers": {
    "knowledge-base": {
      "command": "python",
      "args": ["-m", "knowledge_base.server"],
      "cwd": "~/.claude/knowledge-base",
      "env": {
        "KB_CONFIG": "~/.claude/knowledge-base/config.json"
      }
    }
  }
}
```

**4. Skill Installation** (`~/.claude/skills/kb/SKILL.md`):
```markdown
---
name: kb
description: Manage personal knowledge base
---

# Knowledge Base Management

Commands:
- `/kb-add-repo <url>` - Add GitHub repository
- `/kb-add-url <url>` - Add web page
- `/kb-add-site <url>` - Add documentation site
- `/kb-search <query>` - Search knowledge
- `/kb-list` - List all sources
- `/kb-delete <id>` - Delete source
- `/kb-status` - Show indexing status
```

### Service Management

**Start/Stop**:
```bash
# Method 1: Auto-start by Claude Code (recommended)
# MCP Server auto-runs when Claude Code starts

# Method 2: Manual run (for debugging)
python -m knowledge_base.server --config ~/.claude/knowledge-base/config.json

# View logs
tail -f ~/.claude/knowledge-base/logs/server.log

# Health check
curl http://localhost:8080/health
```

### Data Management

**Backup**:
```bash
# Backup knowledge base
kb-backup --output ~/backups/kb-2026-03-06.tar.gz

# Includes:
# - SQLite database
# - Chroma collection
# - Config files
```

**Migration**:
```bash
# Restore backup
kb-restore ~/backups/kb-2026-03-06.tar.gz

# Export as JSON (for version control)
kb-export --format json --output sources.json
```

## Testing Strategy

### Unit Tests

```python
# tests/test_chunker.py
def test_markdown_chunking_preserves_headers():
    content = """
    # Main Title
    ## Section 1
    Content here...
    ## Section 2
    More content...
    """
    chunks = chunker.chunk_markdown(content, max_size=100)
    assert all("# Main Title" in chunk for chunk in chunks)  # Preserve header context

# tests/test_retriever.py
@pytest.mark.asyncio
async def test_search_with_filter():
    results = await retriever.search(
        "authentication",
        filter={"source_type": "github", "language": "typescript"}
    )
    assert all(r.metadata["language"] == "typescript" for r in results)
```

### Integration Tests

```python
# tests/integration/test_indexing_flow.py
@pytest.mark.integration
async def test_full_github_repo_indexing():
    # Use test repository
    source_id = await indexer.add_github_repo("octocat/Hello-World")

    # Wait for indexing to complete
    await wait_for_status(source_id, "ready", timeout=60)

    # Verify content can be retrieved
    results = await retriever.search("Hello World")
    assert len(results) > 0
    assert any("octocat/Hello-World" in r.metadata["url"] for r in results)
```

### E2E Tests

```python
# tests/e2e/test_mcp_workflow.py
def test_skill_add_and_search():
    # Simulate user using Skill
    result = mcp_client.call_tool("add_github_repo", {
        "repo_url": "vercel/next.js",
        "include": ["docs/**/*.md"]
    })
    assert result["status"] == "indexing"

    # Search after completion
    search_result = mcp_client.call_tool("search_knowledge", {
        "query": "Server Components"
    })
    assert len(search_result["results"]) > 0
```

## Performance Optimization

**1. Batch Processing**:
```python
# Batch generate embeddings (reduce HTTP calls)
async def embed_batch(texts: List[str], batch_size: int = 32):
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        batch_embeddings = await ollama_client.embed(batch)
        embeddings.extend(batch_embeddings)
    return embeddings
```

**2. Caching Strategy**:
```python
# LRU cache for common queries
from functools import lru_cache

@lru_cache(maxsize=100)
def get_query_embedding(query: str) -> List[float]:
    """Cache query embeddings"""
    return ollama_client.embed(query)
```

**3. Concurrency Control**:
```python
# Limit concurrency to avoid overwhelming API
semaphore = asyncio.Semaphore(10)

async def fetch_with_limit(url: str):
    async with semaphore:
        return await fetch(url)
```

## Future Extensibility

### Roadmap

**Phase 1 (MVP)**:
- ✅ GitHub repo indexing
- ✅ Web page/site indexing
- ✅ Basic retrieval and MCP Resource
- ✅ Skill commands

**Phase 2 (Enhancement)**:
- 🔲 Local file/directory indexing
- 🔲 Incremental updates and auto-sync
- 🔲 Multi-language optimization (Chinese word segmentation)
- 🔲 Query reranking (Reranker)
- 🔲 Relevance feedback learning

**Phase 3 (Advanced)**:
- 🔲 GraphRAG (knowledge graph enhancement)
- 🔲 Multi-modal support (images, code screenshots)
- 🔲 Collaborative sharing (team knowledge base)
- 🔲 Auto-summarization and Q&A
- 🔲 Knowledge base analytics and visualization

### Extension Points

**1. Data Source Adapter Interface**:
```python
class SourceAdapter(ABC):
    @abstractmethod
    async def list_files(self) -> List[FileInfo]:
        """List all files"""

    @abstractmethod
    async def download(self, file: FileInfo) -> str:
        """Download file content"""

# Future extensions: GitLabAdapter, NotionAdapter, ConfluenceAdapter
```

**2. Embedding Model Switching**:
```python
class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings"""

# Support switching: OllamaProvider, OpenAIProvider, CohereProvider
```

**3. Chunking Strategy Plugins**:
```python
class ChunkStrategy(ABC):
    @abstractmethod
    def chunk(self, content: str, metadata: dict) -> List[Chunk]:
        """Content chunking"""

# Can register custom strategies: SemanticChunker, RecursiveChunker
```

## Summary

This knowledge base system will:

1. **Run as MCP Server**, providing persistent knowledge storage
2. **Provide convenient commands via Skill**, for daily use
3. **Auto-enhance Claude context**, seamlessly integrated into conversations
4. **Support multiple knowledge sources**: GitHub repos, Web docs, local files
5. **Use Chroma + Ollama**, fully local and free
6. **Smart incremental updates**, avoid redundant indexing
7. **Fault tolerance and error recovery**, ensure data consistency
8. **Extensible architecture**, support future feature enhancements

## Next Steps

1. Create detailed implementation plan
2. Set up project structure
3. Implement Phase 1 (MVP) features
4. Write comprehensive tests
5. Deploy and iterate
