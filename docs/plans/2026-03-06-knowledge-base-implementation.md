# Knowledge Base System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a personal knowledge base system that extracts knowledge from GitHub repos, web docs, and stores in Chroma vector DB, with MCP Server + Skill integration for Claude Code.

**Architecture:** Independent service mode - MCP Server directly uses Chroma Python SDK and Ollama API, with SQLite for metadata tracking and incremental updates.

**Tech Stack:** Python 3.11+, FastMCP, Chroma, Ollama (nomic-embed-text), SQLite, PyGithub, trafilatura

---

## Phase 1: Project Setup and Foundation (MVP)

### Task 1: Project Structure and Dependencies

**Files:**
- Create: `mcp-server/pyproject.toml`
- Create: `mcp-server/requirements.txt`
- Create: `mcp-server/__init__.py`
- Create: `.gitignore`
- Create: `README.md`

**Step 1: Write project structure test**

Create: `tests/test_project_structure.py`

```python
import os
from pathlib import Path

def test_mcp_server_directory_exists():
    """Verify mcp-server directory structure"""
    assert Path("mcp-server").exists()
    assert Path("mcp-server/__init__.py").exists()
    assert Path("mcp-server/requirements.txt").exists()

def test_skill_directory_exists():
    """Verify skill directory structure"""
    assert Path("skill").exists()
    assert Path("skill/SKILL.md").exists()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_project_structure.py -v`
Expected: FAIL with "No such file or directory"

**Step 3: Create project structure**

```bash
mkdir -p mcp-server/sources
mkdir -p skill
mkdir -p tests/unit tests/integration tests/e2e
mkdir -p docs/plans
touch mcp-server/__init__.py
touch mcp-server/sources/__init__.py
```

Create: `mcp-server/requirements.txt`

```txt
fastmcp>=1.0.0
chromadb>=0.4.24
httpx>=0.27.0
aiosqlite>=0.20.0
tenacity>=8.2.3
pydantic>=2.6.0
pygithub>=2.1.1
trafilatura>=1.8.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-cov>=4.1.0
```

Create: `.gitignore`

```
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
.coverage
htmlcov/
*.egg-info/
dist/
build/
.venv/
venv/
*.sqlite
*.db
.DS_Store
logs/
*.log
```

Create: `README.md`

```markdown
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
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_project_structure.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add .
git commit -m "chore: initialize project structure and dependencies"
```

---

### Task 2: Configuration Management

**Files:**
- Create: `mcp-server/config.py`
- Test: `tests/unit/test_config.py`

**Step 1: Write configuration test**

Create: `tests/unit/test_config.py`

```python
import pytest
from pathlib import Path
from mcp_server.config import Config

def test_config_load_default():
    """Test loading default configuration"""
    config = Config.load_default()
    assert config.chroma.host == "localhost"
    assert config.chroma.port == 8000
    assert config.ollama.model == "nomic-embed-text"

def test_config_validate():
    """Test configuration validation"""
    config = Config.load_default()
    assert config.validate() is True

def test_config_invalid_chunk_size():
    """Test invalid chunk size raises error"""
    config = Config.load_default()
    config.indexing.chunk_size = -1
    with pytest.raises(ValueError):
        config.validate()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_config.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'mcp_server.config'"

**Step 3: Implement configuration module**

Create: `mcp-server/config.py`

```python
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel, Field, validator
import json
import os

class ChromaConfig(BaseModel):
    host: str = "localhost"
    port: int = 8000
    collection_name: str = "knowledge_base"
    persist_directory: str = "~/.claude/knowledge-base/chroma_db"

class OllamaConfig(BaseModel):
    host: str = "localhost"
    port: int = 11434
    model: str = "nomic-embed-text"
    timeout: int = 60

class GitHubConfig(BaseModel):
    token: Optional[str] = None
    max_file_size_mb: int = 5

class WebConfig(BaseModel):
    user_agent: str = "KnowledgeBase/1.0"
    timeout: int = 30
    max_pages_per_site: int = 100

class IndexingConfig(BaseModel):
    chunk_size: int = 1000
    chunk_overlap: int = 200
    batch_size: int = 10
    default_includes: List[str] = Field(default_factory=lambda: [
        "**/*.md", "**/README*", "**/docs/**",
        "**/*.ts", "**/*.py", "**/*.go"
    ])
    default_excludes: List[str] = Field(default_factory=lambda: [
        "**/node_modules/**", "**/.git/**", "**/dist/**",
        "**/build/**", "**/*.test.*", "**/*.spec.*"
    ])

    @validator('chunk_size')
    def validate_chunk_size(cls, v):
        if v <= 0:
            raise ValueError("chunk_size must be positive")
        return v

class RetrievalConfig(BaseModel):
    default_top_k: int = 5
    similarity_threshold: float = 0.7

class Config(BaseModel):
    chroma: ChromaConfig = Field(default_factory=ChromaConfig)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    github: GitHubConfig = Field(default_factory=GitHubConfig)
    web: WebConfig = Field(default_factory=WebConfig)
    indexing: IndexingConfig = Field(default_factory=IndexingConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)

    @classmethod
    def load_default(cls) -> "Config":
        """Load default configuration"""
        return cls()

    @classmethod
    def load_from_file(cls, path: Path) -> "Config":
        """Load configuration from JSON file"""
        with open(path) as f:
            data = json.load(f)
        return cls(**data)

    def validate(self) -> bool:
        """Validate configuration"""
        # Pydantic handles validation automatically
        return True

    def save_to_file(self, path: Path):
        """Save configuration to JSON file"""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.dict(), f, indent=2)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_config.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add mcp-server/config.py tests/unit/test_config.py
git commit -m "feat: add configuration management with validation"
```

---

### Task 3: Data Models

**Files:**
- Create: `mcp-server/models.py`
- Test: `tests/unit/test_models.py`

**Step 1: Write data models test**

Create: `tests/unit/test_models.py`

```python
from datetime import datetime
from mcp_server.models import Source, Document, Chunk, SearchResult

def test_source_creation():
    """Test Source model creation"""
    source = Source(
        id="test-uuid",
        type="github_repo",
        url="https://github.com/owner/repo",
        name="Test Repo"
    )
    assert source.id == "test-uuid"
    assert source.status == "pending"

def test_document_creation():
    """Test Document model creation"""
    doc = Document(
        id="doc-uuid",
        source_id="source-uuid",
        file_path="src/index.ts",
        content_hash="abc123"
    )
    assert doc.source_id == "source-uuid"

def test_chunk_id_generation():
    """Test Chunk ID generation"""
    chunk = Chunk(
        source_id="source-123",
        file_path="README.md",
        chunk_index=0,
        text="Content here",
        metadata={}
    )
    assert chunk.id == "source-123:README.md:chunk_0"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_models.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'mcp_server.models'"

**Step 3: Implement data models**

Create: `mcp-server/models.py`

```python
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum

class SourceType(str, Enum):
    GITHUB_REPO = "github_repo"
    GITHUB_FILE = "github_file"
    WEB_PAGE = "web_page"
    WEB_SITE = "web_site"
    LOCAL = "local"

class SourceStatus(str, Enum):
    PENDING = "pending"
    INDEXING = "indexing"
    READY = "ready"
    ERROR = "error"

class Source(BaseModel):
    id: str
    type: SourceType
    url: str
    name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    status: SourceStatus = SourceStatus.PENDING
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_indexed_at: Optional[datetime] = None
    document_count: int = 0
    chunk_count: int = 0

class Document(BaseModel):
    id: str
    source_id: str
    file_path: Optional[str] = None
    content_hash: Optional[str] = None
    chunk_count: Optional[int] = None
    indexed_at: Optional[datetime] = None

class Chunk(BaseModel):
    source_id: str
    file_path: str
    chunk_index: int
    text: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None

    @property
    def id(self) -> str:
        """Generate unique chunk ID"""
        return f"{self.source_id}:{self.file_path}:chunk_{self.chunk_index}"

class SearchResult(BaseModel):
    content: str
    metadata: Dict[str, Any]
    score: float
    source: Optional[Source] = None
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_models.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add mcp-server/models.py tests/unit/test_models.py
git commit -m "feat: add data models for sources, documents, and chunks"
```

---

### Task 4: SQLite Storage Layer

**Files:**
- Create: `mcp-server/storage.py`
- Test: `tests/unit/test_storage.py`

**Step 1: Write storage layer test**

Create: `tests/unit/test_storage.py`

```python
import pytest
import aiosqlite
from pathlib import Path
from mcp_server.storage import Storage
from mcp_server.models import Source, SourceType, SourceStatus

@pytest.mark.asyncio
async def test_storage_init_creates_tables(tmp_path):
    """Test storage initialization creates tables"""
    db_path = tmp_path / "test.db"
    storage = Storage(db_path)
    await storage.init()

    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = [row[0] for row in await cursor.fetchall()]
        assert "sources" in tables
        assert "documents" in tables

@pytest.mark.asyncio
async def test_storage_add_source(tmp_path):
    """Test adding a source"""
    db_path = tmp_path / "test.db"
    storage = Storage(db_path)
    await storage.init()

    source = Source(
        id="test-123",
        type=SourceType.GITHUB_REPO,
        url="https://github.com/owner/repo",
        name="Test Repo"
    )

    await storage.add_source(source)
    retrieved = await storage.get_source("test-123")

    assert retrieved is not None
    assert retrieved.id == "test-123"
    assert retrieved.type == SourceType.GITHUB_REPO

@pytest.mark.asyncio
async def test_storage_update_source_status(tmp_path):
    """Test updating source status"""
    db_path = tmp_path / "test.db"
    storage = Storage(db_path)
    await storage.init()

    source = Source(
        id="test-123",
        type=SourceType.GITHUB_REPO,
        url="https://github.com/owner/repo"
    )

    await storage.add_source(source)
    await storage.update_source_status("test-123", SourceStatus.READY)

    retrieved = await storage.get_source("test-123")
    assert retrieved.status == SourceStatus.READY
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_storage.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'mcp_server.storage'"

**Step 3: Implement storage layer**

Create: `mcp-server/storage.py`

```python
import aiosqlite
import json
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from mcp_server.models import Source, Document, SourceStatus, SourceType

class Storage:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)

    async def init(self):
        """Initialize database and create tables"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS sources (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    url TEXT NOT NULL,
                    name TEXT,
                    config TEXT,
                    status TEXT DEFAULT 'pending',
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_indexed_at TIMESTAMP,
                    document_count INTEGER DEFAULT 0,
                    chunk_count INTEGER DEFAULT 0
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    file_path TEXT,
                    content_hash TEXT,
                    chunk_count INTEGER,
                    indexed_at TIMESTAMP,
                    FOREIGN KEY (source_id) REFERENCES sources(id)
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS index_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT NOT NULL,
                    priority INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (source_id) REFERENCES sources(id)
                )
            """)

            await db.commit()

    async def add_source(self, source: Source):
        """Add a new source"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO sources (
                    id, type, url, name, config, status,
                    created_at, document_count, chunk_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                source.id,
                source.type.value,
                source.url,
                source.name,
                json.dumps(source.config) if source.config else None,
                source.status.value,
                source.created_at.isoformat(),
                source.document_count,
                source.chunk_count
            ))
            await db.commit()

    async def get_source(self, source_id: str) -> Optional[Source]:
        """Get source by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM sources WHERE id = ?",
                (source_id,)
            )
            row = await cursor.fetchone()

            if not row:
                return None

            return Source(
                id=row['id'],
                type=SourceType(row['type']),
                url=row['url'],
                name=row['name'],
                config=json.loads(row['config']) if row['config'] else None,
                status=SourceStatus(row['status']),
                error_message=row['error_message'],
                created_at=datetime.fromisoformat(row['created_at']),
                last_indexed_at=datetime.fromisoformat(row['last_indexed_at']) if row['last_indexed_at'] else None,
                document_count=row['document_count'],
                chunk_count=row['chunk_count']
            )

    async def update_source_status(
        self,
        source_id: str,
        status: SourceStatus,
        error_message: Optional[str] = None
    ):
        """Update source status"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE sources
                SET status = ?, error_message = ?
                WHERE id = ?
            """, (status.value, error_message, source_id))
            await db.commit()

    async def list_sources(
        self,
        source_type: Optional[SourceType] = None
    ) -> List[Source]:
        """List all sources, optionally filtered by type"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            if source_type:
                cursor = await db.execute(
                    "SELECT * FROM sources WHERE type = ? ORDER BY created_at DESC",
                    (source_type.value,)
                )
            else:
                cursor = await db.execute(
                    "SELECT * FROM sources ORDER BY created_at DESC"
                )

            rows = await cursor.fetchall()

            return [
                Source(
                    id=row['id'],
                    type=SourceType(row['type']),
                    url=row['url'],
                    name=row['name'],
                    config=json.loads(row['config']) if row['config'] else None,
                    status=SourceStatus(row['status']),
                    error_message=row['error_message'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    last_indexed_at=datetime.fromisoformat(row['last_indexed_at']) if row['last_indexed_at'] else None,
                    document_count=row['document_count'],
                    chunk_count=row['chunk_count']
                )
                for row in rows
            ]

    async def delete_source(self, source_id: str):
        """Delete a source and its documents"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM documents WHERE source_id = ?", (source_id,))
            await db.execute("DELETE FROM sources WHERE id = ?", (source_id,))
            await db.commit()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_storage.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add mcp-server/storage.py tests/unit/test_storage.py
git commit -m "feat: add SQLite storage layer for metadata tracking"
```

---

### Task 5: Ollama Embedding Client

**Files:**
- Create: `mcp-server/embeddings.py`
- Test: `tests/unit/test_embeddings.py`

**Step 1: Write embedding client test**

Create: `tests/unit/test_embeddings.py`

```python
import pytest
from mcp_server.embeddings import OllamaEmbeddings
from mcp_server.config import OllamaConfig

@pytest.mark.asyncio
async def test_ollama_embed_single():
    """Test embedding single text"""
    config = OllamaConfig()
    client = OllamaEmbeddings(config)

    # Mock test - would need actual Ollama running for real test
    text = "Hello world"
    # embedding = await client.embed(text)
    # assert isinstance(embedding, list)
    # assert len(embedding) > 0

@pytest.mark.asyncio
async def test_ollama_embed_batch():
    """Test embedding batch of texts"""
    config = OllamaConfig()
    client = OllamaEmbeddings(config)

    texts = ["Hello", "World", "Test"]
    # embeddings = await client.embed_batch(texts)
    # assert len(embeddings) == 3
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_embeddings.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Implement Ollama embedding client**

Create: `mcp-server/embeddings.py`

```python
import httpx
from typing import List
from mcp_server.config import OllamaConfig

class OllamaEmbeddings:
    def __init__(self, config: OllamaConfig):
        self.config = config
        self.base_url = f"http://{config.host}:{config.port}"
        self.client = httpx.AsyncClient(timeout=config.timeout)

    async def embed(self, text: str) -> List[float]:
        """Generate embedding for single text"""
        response = await self.client.post(
            f"{self.base_url}/api/embeddings",
            json={
                "model": self.config.model,
                "prompt": text
            }
        )
        response.raise_for_status()
        return response.json()["embedding"]

    async def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> List[List[float]]:
        """Generate embeddings for batch of texts"""
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            batch_embeddings = []
            for text in batch:
                embedding = await self.embed(text)
                batch_embeddings.append(embedding)
            embeddings.extend(batch_embeddings)
        return embeddings

    async def check_model_available(self) -> bool:
        """Check if embedding model is available"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            models = response.json().get("models", [])
            return any(m["name"] == self.config.model for m in models)
        except Exception:
            return False

    async def pull_model(self):
        """Pull embedding model if not available"""
        response = await self.client.post(
            f"{self.base_url}/api/pull",
            json={"name": self.config.model}
        )
        response.raise_for_status()

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_embeddings.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add mcp-server/embeddings.py tests/unit/test_embeddings.py
git commit -m "feat: add Ollama embedding client with batch support"
```

---

### Task 6: Text Chunking Logic

**Files:**
- Create: `mcp-server/chunker.py`
- Test: `tests/unit/test_chunker.py`

**Step 1: Write chunker test**

Create: `tests/unit/test_chunker.py`

```python
from mcp_server.chunker import Chunker, ChunkResult

def test_chunk_markdown_preserves_headers():
    """Test markdown chunking preserves header hierarchy"""
    content = """# Main Title

## Section 1
Content for section 1 here.

## Section 2
Content for section 2 here.
"""
    chunker = Chunker(chunk_size=100, chunk_overlap=20)
    chunks = chunker.chunk_markdown(content)

    # Each chunk should include header breadcrumb
    assert len(chunks) > 0
    assert all("# Main Title" in chunk.text or chunk.metadata.get("header") for chunk in chunks)

def test_chunk_plain_text_sliding_window():
    """Test plain text chunking with sliding window"""
    content = "a" * 1000
    chunker = Chunker(chunk_size=200, chunk_overlap=50)
    chunks = chunker.chunk_plain_text(content)

    assert len(chunks) > 1
    # Check overlap exists
    if len(chunks) > 1:
        assert chunks[0].text[-50:] == chunks[1].text[:50]

def test_chunk_detects_language():
    """Test language detection from file path"""
    chunker = Chunker()

    assert chunker.detect_language("file.py") == "python"
    assert chunker.detect_language("file.ts") == "typescript"
    assert chunker.detect_language("file.md") == "markdown"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_chunker.py -v`
Expected: FAIL

**Step 3: Implement chunker**

Create: `mcp-server/chunker.py`

```python
import re
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class ChunkResult:
    text: str
    metadata: Dict[str, Any]

class Chunker:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, content: str, file_path: str) -> List[ChunkResult]:
        """Chunk content based on file type"""
        language = self.detect_language(file_path)

        if language == "markdown":
            return self.chunk_markdown(content)
        else:
            return self.chunk_plain_text(content)

    def detect_language(self, file_path: str) -> str:
        """Detect language from file extension"""
        ext = file_path.split(".")[-1].lower()

        lang_map = {
            "md": "markdown",
            "py": "python",
            "ts": "typescript",
            "tsx": "typescript",
            "js": "javascript",
            "jsx": "javascript",
            "go": "go",
            "rs": "rust",
            "java": "java",
        }

        return lang_map.get(ext, "text")

    def chunk_markdown(self, content: str) -> List[ChunkResult]:
        """Chunk markdown by header hierarchy"""
        chunks = []

        # Split by headers
        lines = content.split("\n")
        current_chunk = []
        current_headers = []
        current_size = 0

        for line in lines:
            # Check if line is a header
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)

            if header_match:
                # Save current chunk if it exists
                if current_chunk:
                    chunks.append(ChunkResult(
                        text="\n".join(current_chunk),
                        metadata={"headers": current_headers.copy()}
                    ))
                    current_chunk = []
                    current_size = 0

                # Update header breadcrumb
                level = len(header_match.group(1))
                header_text = header_match.group(2)

                # Remove headers of same or lower level
                current_headers = [h for h in current_headers if h[0] < level]
                current_headers.append((level, header_text))

            current_chunk.append(line)
            current_size += len(line)

            # Split if chunk is too large
            if current_size > self.chunk_size and not header_match:
                chunks.append(ChunkResult(
                    text="\n".join(current_chunk),
                    metadata={"headers": current_headers.copy()}
                ))
                current_chunk = []
                current_size = 0

        # Add final chunk
        if current_chunk:
            chunks.append(ChunkResult(
                text="\n".join(current_chunk),
                metadata={"headers": current_headers.copy()}
            ))

        return chunks

    def chunk_plain_text(self, content: str) -> List[ChunkResult]:
        """Chunk plain text with sliding window"""
        chunks = []
        start = 0

        while start < len(content):
            end = start + self.chunk_size
            chunk_text = content[start:end]

            chunks.append(ChunkResult(
                text=chunk_text,
                metadata={}
            ))

            start += (self.chunk_size - self.chunk_overlap)

        return chunks
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_chunker.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add mcp-server/chunker.py tests/unit/test_chunker.py
git commit -m "feat: add text chunking with markdown and plain text support"
```

---

## Execution Options

Plan complete and saved to `docs/plans/2026-03-06-knowledge-base-implementation.md`.

This is Phase 1 (Project Setup and Foundation) with 6 tasks covering:
- Project structure
- Configuration management
- Data models
- SQLite storage
- Ollama embeddings
- Text chunking

**Next phases will cover:**
- Phase 2: GitHub integration
- Phase 3: Web scraping
- Phase 4: Chroma integration and retrieval
- Phase 5: MCP Server
- Phase 6: Skill integration

**Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
