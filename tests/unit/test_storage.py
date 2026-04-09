import pytest
import aiosqlite
from datetime import datetime, timezone
from pathlib import Path
from kb.core.storage import Storage
from kb.core.models import Document, Source, SourceType, SourceStatus

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
async def test_storage_init_migrates_legacy_sources_table(tmp_path):
    """Test storage initialization migrates older sources schemas."""
    db_path = tmp_path / "legacy.db"
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE sources (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                url TEXT NOT NULL,
                name TEXT,
                config TEXT,
                status TEXT DEFAULT 'pending',
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

    storage = Storage(db_path)
    await storage.init()

    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("PRAGMA table_info(sources)")
        columns = {row[1] for row in await cursor.fetchall()}

    assert "last_indexed_at" in columns
    assert "document_count" in columns
    assert "chunk_count" in columns

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


@pytest.mark.asyncio
async def test_storage_update_source_status_with_stats(tmp_path):
    """Test updating source status with indexing metadata."""
    db_path = tmp_path / "test.db"
    storage = Storage(db_path)
    await storage.init()

    source = Source(
        id="local:/tmp/example",
        type=SourceType.LOCAL,
        url="/tmp/example"
    )

    await storage.add_source(source)
    indexed_at = datetime.now(timezone.utc)
    await storage.update_source_status(
        "local:/tmp/example",
        SourceStatus.READY,
        last_indexed_at=indexed_at,
        document_count=2,
        chunk_count=5,
    )

    retrieved = await storage.get_source("local:/tmp/example")
    assert retrieved is not None
    assert retrieved.last_indexed_at == indexed_at
    assert retrieved.document_count == 2
    assert retrieved.chunk_count == 5


@pytest.mark.asyncio
async def test_storage_update_document_indexing(tmp_path):
    """Test updating document indexing metadata."""
    db_path = tmp_path / "test.db"
    storage = Storage(db_path)
    await storage.init()

    source = Source(
        id="local:/tmp/example",
        type=SourceType.LOCAL,
        url="/tmp/example"
    )
    await storage.add_source(source)

    document = Document(
        id="local:/tmp/example:file.txt",
        source_id="local:/tmp/example",
        file_path="file.txt",
        content_hash="abc123",
    )
    await storage.add_document(document)

    indexed_at = datetime.now(timezone.utc)
    await storage.update_document_indexing(document.id, 3, indexed_at)

    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "SELECT chunk_count, indexed_at FROM documents WHERE id = ?",
            (document.id,),
        )
        row = await cursor.fetchone()

    assert row is not None
    assert row[0] == 3
    assert row[1] == indexed_at.isoformat()
