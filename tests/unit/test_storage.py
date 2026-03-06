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