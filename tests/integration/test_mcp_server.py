"""Integration tests for MCP Server."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestMCPServer:
    """Test class for MCP server."""

    @pytest.mark.asyncio
    async def test_server_creation(self):
        """Test that server can be created"""
        # Mock Storage, Indexer, and Retriever initialization
        with patch('mcp_server.server.Storage') as mock_storage_class, \
             patch('mcp_server.server.Indexer') as mock_indexer_class, \
             patch('mcp_server.server.Retriever') as mock_retriever_class, \
             patch('mcp_server.server.Config') as mock_config_class, \
             patch('mcp_server.indexer.ChromaClient'), \
             patch('mcp_server.retriever.ChromaClient'):

            # Setup mock instances
            mock_config = MagicMock()
            mock_config_class.load_from_file.return_value = mock_config

            # Mock storage with async methods
            mock_storage = MagicMock()
            mock_storage.init = AsyncMock()
            mock_storage_class.return_value = mock_storage

            # Mock indexer with async init
            mock_indexer = MagicMock()
            mock_indexer.initialize = AsyncMock()
            mock_indexer_class.return_value = mock_indexer

            mock_retriever_class.return_value = MagicMock()

            from mcp_server.server import create_server

            mcp = create_server()
            assert mcp is not None
            assert hasattr(mcp, 'tool')

    @pytest.mark.asyncio
    async def test_server_tools_registered(self):
        """Test that all tools are registered"""
        with patch('mcp_server.server.Storage') as mock_storage_class, \
             patch('mcp_server.server.Indexer') as mock_indexer_class, \
             patch('mcp_server.server.Retriever') as mock_retriever_class, \
             patch('mcp_server.server.Config') as mock_config_class, \
             patch('mcp_server.indexer.ChromaClient'), \
             patch('mcp_server.retriever.ChromaClient'):

            mock_config_class.load_from_file.return_value = MagicMock()
            mock_storage_class.return_value = MagicMock()
            mock_indexer_class.return_value = MagicMock()
            mock_retriever_class.return_value = MagicMock()

            from mcp_server.server import create_server

            mcp = create_server()

            # Get registered tools using async list_tools method
            tools = await mcp.list_tools()
            tool_names = [tool.name for tool in tools]

            # Verify expected tools are registered
            expected_tools = [
                'kb_add_repo',
                'kb_add_url',
                'kb_add_site',
                'kb_search',
                'kb_list',
                'kb_delete',
                'kb_status',
            ]

            for tool in expected_tools:
                assert tool in tool_names, f"Tool {tool} not registered"

    @pytest.mark.asyncio
    async def test_kb_add_repo_tool_exists(self):
        """Test kb_add_repo tool is properly defined"""
        with patch('mcp_server.server.Storage') as mock_storage_class, \
             patch('mcp_server.server.Indexer') as mock_indexer_class, \
             patch('mcp_server.server.Retriever') as mock_retriever_class, \
             patch('mcp_server.server.Config') as mock_config_class, \
             patch('mcp_server.indexer.ChromaClient'), \
             patch('mcp_server.retriever.ChromaClient'):

            mock_config_class.load_from_file.return_value = MagicMock()
            mock_storage_class.return_value = MagicMock()
            mock_indexer_class.return_value = MagicMock()
            mock_retriever_class.return_value = MagicMock()

            from mcp_server.server import create_server

            mcp = create_server()

            # Find kb_add_repo tool
            tools = await mcp.list_tools()
            kb_add_repo = next((t for t in tools if t.name == 'kb_add_repo'), None)
            assert kb_add_repo is not None

    @pytest.mark.asyncio
    async def test_kb_search_tool_exists(self):
        """Test kb_search tool is properly defined"""
        with patch('mcp_server.server.Storage') as mock_storage_class, \
             patch('mcp_server.server.Indexer') as mock_indexer_class, \
             patch('mcp_server.server.Retriever') as mock_retriever_class, \
             patch('mcp_server.server.Config') as mock_config_class, \
             patch('mcp_server.indexer.ChromaClient'), \
             patch('mcp_server.retriever.ChromaClient'):

            mock_config_class.load_from_file.return_value = MagicMock()
            mock_storage_class.return_value = MagicMock()
            mock_indexer_class.return_value = MagicMock()
            mock_retriever_class.return_value = MagicMock()

            from mcp_server.server import create_server

            mcp = create_server()

            # Find kb_search tool
            tools = await mcp.list_tools()
            kb_search = next((t for t in tools if t.name == 'kb_search'), None)
            assert kb_search is not None

    @pytest.mark.asyncio
    async def test_kb_list_tool_exists(self):
        """Test kb_list tool is properly defined"""
        with patch('mcp_server.server.Storage') as mock_storage_class, \
             patch('mcp_server.server.Indexer') as mock_indexer_class, \
             patch('mcp_server.server.Retriever') as mock_retriever_class, \
             patch('mcp_server.server.Config') as mock_config_class, \
             patch('mcp_server.indexer.ChromaClient'), \
             patch('mcp_server.retriever.ChromaClient'):

            mock_config_class.load_from_file.return_value = MagicMock()
            mock_storage_class.return_value = MagicMock()
            mock_indexer_class.return_value = MagicMock()
            mock_retriever_class.return_value = MagicMock()

            from mcp_server.server import create_server

            mcp = create_server()

            # Find kb_list tool
            tools = await mcp.list_tools()
            kb_list = next((t for t in tools if t.name == 'kb_list'), None)
            assert kb_list is not None

    @pytest.mark.asyncio
    async def test_kb_status_tool_exists(self):
        """Test kb_status tool is properly defined"""
        with patch('mcp_server.server.Storage') as mock_storage_class, \
             patch('mcp_server.server.Indexer') as mock_indexer_class, \
             patch('mcp_server.server.Retriever') as mock_retriever_class, \
             patch('mcp_server.server.Config') as mock_config_class, \
             patch('mcp_server.indexer.ChromaClient'), \
             patch('mcp_server.retriever.ChromaClient'):

            mock_config_class.load_from_file.return_value = MagicMock()
            mock_storage_class.return_value = MagicMock()
            mock_indexer_class.return_value = MagicMock()
            mock_retriever_class.return_value = MagicMock()

            from mcp_server.server import create_server

            mcp = create_server()

            # Find kb_status tool
            tools = await mcp.list_tools()
            kb_status = next((t for t in tools if t.name == 'kb_status'), None)
            assert kb_status is not None

    @pytest.mark.asyncio
    async def test_kb_delete_tool_exists(self):
        """Test kb_delete tool is properly defined"""
        with patch('mcp_server.server.Storage') as mock_storage_class, \
             patch('mcp_server.server.Indexer') as mock_indexer_class, \
             patch('mcp_server.server.Retriever') as mock_retriever_class, \
             patch('mcp_server.server.Config') as mock_config_class, \
             patch('mcp_server.indexer.ChromaClient'), \
             patch('mcp_server.retriever.ChromaClient'):

            mock_config_class.load_from_file.return_value = MagicMock()
            mock_storage_class.return_value = MagicMock()
            mock_indexer_class.return_value = MagicMock()
            mock_retriever_class.return_value = MagicMock()

            from mcp_server.server import create_server

            mcp = create_server()

            # Find kb_delete tool
            tools = await mcp.list_tools()
            kb_delete = next((t for t in tools if t.name == 'kb_delete'), None)
            assert kb_delete is not None


class TestStorageDocumentCount:
    """Test get_document_count method in Storage."""

    @pytest.mark.asyncio
    async def test_get_document_count_method_exists(self):
        """Test Storage has get_document_count method"""
        from mcp_server.storage import Storage
        from pathlib import Path

        storage = Storage(Path("/tmp/test_storage.db"))
        assert hasattr(storage, 'get_document_count')
        assert callable(storage.get_document_count)

    @pytest.mark.asyncio
    async def test_get_document_count_returns_zero_for_empty(self):
        """Test get_document_count returns 0 for empty database"""
        import asyncio
        from mcp_server.storage import Storage
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            storage = Storage(Path(tmpdir) / "test.db")
            await storage.init()

            count = await storage.get_document_count()
            assert count == 0

    @pytest.mark.asyncio
    async def test_get_document_count_returns_correct_value(self):
        """Test get_document_count returns correct count after adding documents"""
        import asyncio
        from mcp_server.storage import Storage
        from mcp_server.models import Document
        from pathlib import Path
        import tempfile
        from datetime import datetime, timezone

        with tempfile.TemporaryDirectory() as tmpdir:
            storage = Storage(Path(tmpdir) / "test.db")
            await storage.init()

            # Add some documents
            for i in range(3):
                doc = Document(
                    id=f"doc_{i}",
                    source_id="test_source",
                    file_path=f"/path/to/file_{i}.txt",
                    content_hash=f"hash_{i}",
                    chunk_count=i + 1,
                    indexed_at=datetime.now(timezone.utc)
                )
                await storage.add_document(doc)

            count = await storage.get_document_count()
            assert count == 3