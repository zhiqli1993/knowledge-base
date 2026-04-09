"""Integration tests for MCP proxy server."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.add_repo = AsyncMock(return_value={"message": "Indexing started", "source": {"id": "github:test/repo", "name": "repo", "type": "github_repo", "url": "https://github.com/test/repo", "status": "pending", "document_count": 0, "chunk_count": 0, "progress_total": 0, "progress_processed": 0}})
    client.add_url = AsyncMock(return_value={"message": "Indexing started", "source": {"id": "web:example.com", "name": "url", "type": "web_page", "url": "https://example.com", "status": "pending", "document_count": 0, "chunk_count": 0, "progress_total": 0, "progress_processed": 0}})
    client.add_local = AsyncMock(return_value={"message": "Indexing started", "source": {"id": "local:/tmp/demo", "name": "demo", "type": "local", "url": "/tmp/demo", "status": "pending", "document_count": 0, "chunk_count": 0, "progress_total": 0, "progress_processed": 0}})
    client.add_site = AsyncMock(return_value={"message": "Indexing started", "source": {"id": "site:example.com", "name": "site", "type": "web_site", "url": "https://example.com", "status": "pending", "document_count": 0, "chunk_count": 0, "progress_total": 0, "progress_processed": 0}})
    client.search = AsyncMock(return_value={"results": []})
    client.list_sources = AsyncMock(return_value={"sources": []})
    client.delete = AsyncMock(return_value={"deleted": True})
    client.status = AsyncMock(return_value={"sources": {"total": 0, "indexed": 0, "indexing": 0, "pending": 0, "failed": 0}, "documents": 0, "chunks": 0, "storage": "/tmp/chroma", "embedding_model": "nomic-embed-text", "service": {"base_url": "http://127.0.0.1:8864"}})
    client.progress = AsyncMock(return_value={"source": {"id": "local:/tmp/demo", "name": "demo", "type": "local", "url": "/tmp/demo", "status": "indexing", "document_count": 1, "chunk_count": 2, "progress_total": 5, "progress_processed": 2, "progress_phase": "indexing", "progress_message": "Working"}})
    client.update = AsyncMock(return_value={"message": "Reindex started"})
    client.reindex = AsyncMock(return_value={"message": "Reindex started"})
    return client


class TestMCPServer:
    @pytest.mark.asyncio
    async def test_server_creation(self, mock_client):
        with patch('kb.mcp.server.KBHttpClient', return_value=mock_client):
            from kb.mcp.server import create_server
            mcp = create_server()
            assert mcp is not None
            assert hasattr(mcp, 'tool')

    @pytest.mark.asyncio
    async def test_server_tools_registered(self, mock_client):
        with patch('kb.mcp.server.KBHttpClient', return_value=mock_client):
            from kb.mcp.server import create_server
            mcp = create_server()
            tools = await mcp.list_tools()
            tool_names = [tool.name for tool in tools]
            expected_tools = [
                'kb_add_repo', 'kb_add_url', 'kb_add_local', 'kb_add_site',
                'kb_search', 'kb_list', 'kb_delete', 'kb_status',
                'kb_progress', 'kb_update', 'kb_reindex',
            ]
            for tool in expected_tools:
                assert tool in tool_names

    @pytest.mark.asyncio
    async def test_tools_exist(self, mock_client):
        with patch('kb.mcp.server.KBHttpClient', return_value=mock_client):
            from kb.mcp.server import create_server
            mcp = create_server()
            tools = {tool.name for tool in await mcp.list_tools()}
            for name in ['kb_add_repo', 'kb_search', 'kb_list', 'kb_status', 'kb_delete']:
                assert name in tools


class TestStorageDocumentCount:
    @pytest.mark.asyncio
    async def test_get_document_count_method_exists(self):
        from kb.core.storage import Storage
        from pathlib import Path

        storage = Storage(Path('/tmp/test_storage.db'))
        assert hasattr(storage, 'get_document_count')
        assert callable(storage.get_document_count)

    @pytest.mark.asyncio
    async def test_get_document_count_returns_zero_for_empty(self):
        from kb.core.storage import Storage
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            storage = Storage(Path(tmpdir) / 'test.db')
            await storage.init()
            count = await storage.get_document_count()
            assert count == 0

    @pytest.mark.asyncio
    async def test_get_document_count_returns_correct_value(self):
        from kb.core.storage import Storage
        from kb.core.models import Document
        from pathlib import Path
        import tempfile
        from datetime import datetime, timezone

        with tempfile.TemporaryDirectory() as tmpdir:
            storage = Storage(Path(tmpdir) / 'test.db')
            await storage.init()
            for i in range(3):
                doc = Document(
                    id=f'doc_{i}',
                    source_id='test_source',
                    file_path=f'/path/to/file_{i}.txt',
                    content_hash=f'hash_{i}',
                    chunk_count=i + 1,
                    indexed_at=datetime.now(timezone.utc),
                )
                await storage.add_document(doc)
            count = await storage.get_document_count()
            assert count == 3
