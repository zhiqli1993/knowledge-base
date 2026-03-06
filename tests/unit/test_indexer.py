import pytest
from unittest.mock import Mock, AsyncMock, patch
from mcp_server.indexer import Indexer
from mcp_server.config import Config
from mcp_server.models import Source, SourceType, SourceStatus


@pytest.fixture
def config():
    """Create test configuration"""
    return Config()


@pytest.fixture
def indexer(config):
    """Create indexer instance with mocked dependencies"""
    with patch.object(Indexer, 'initialize', new_callable=AsyncMock):
        indexer = Indexer(config)
        # Replace real storage with properly mocked async methods
        mock_storage = Mock()
        mock_storage.update_source_status = AsyncMock()
        mock_storage.add_source = AsyncMock()
        mock_storage.add_document = AsyncMock()
        indexer.storage = mock_storage
        return indexer


@pytest.mark.asyncio
async def test_index_github_repo(indexer):
    """Test complete GitHub repo indexing pipeline"""
    with patch('mcp_server.indexer.GitHubRepoFetcher') as mock_fetcher_class, \
         patch.object(indexer.chroma, 'add_documents') as mock_add_chroma, \
         patch.object(indexer.embeddings, 'embed_batch', new_callable=AsyncMock) as mock_embed:

        # Setup mocks
        mock_file_info = Mock()
        mock_file_info.path = "README.md"
        mock_file_info.url = "https://github.com/owner/repo/README.md"
        mock_file_info.language = "markdown"
        mock_file_info.size = 100
        mock_file_info.sha = "abc123"
        mock_file_info.download = AsyncMock(return_value="# Test\n\nContent")

        mock_fetcher = Mock()
        mock_fetcher.list_files = AsyncMock(return_value=[mock_file_info])
        mock_fetcher.close = Mock()
        mock_fetcher_class.return_value = mock_fetcher

        mock_embed.return_value = [[0.1, 0.2, 0.3]]

        source = Source(
            id="github:owner/repo",
            type=SourceType.GITHUB_REPO,
            url="https://github.com/owner/repo",
            status=SourceStatus.PENDING
        )

        # Act
        await indexer.index_source(source)

        # Assert
        assert mock_add_chroma.called


@pytest.mark.asyncio
async def test_index_web_page(indexer):
    """Test web page indexing"""
    with patch('mcp_server.indexer.WebPageFetcher') as mock_fetcher_class, \
         patch.object(indexer.chroma, 'add_documents') as mock_add_chroma, \
         patch.object(indexer.embeddings, 'embed_batch', new_callable=AsyncMock) as mock_embed:

        mock_fetcher = Mock()
        mock_fetcher.fetch_content = AsyncMock(return_value="Test article content")
        mock_fetcher_class.return_value = mock_fetcher

        mock_embed.return_value = [[0.1, 0.2, 0.3]]

        source = Source(
            id="web:example.com/article",
            type=SourceType.WEB_PAGE,
            url="https://example.com/article",
            status=SourceStatus.PENDING
        )

        await indexer.index_source(source)
        assert mock_add_chroma.called


@pytest.mark.asyncio
async def test_index_web_site(indexer):
    """Test website indexing via sitemap"""
    with patch('mcp_server.indexer.WebSiteFetcher') as mock_site_fetcher_class, \
         patch('mcp_server.indexer.WebPageFetcher') as mock_page_fetcher_class, \
         patch.object(indexer.chroma, 'add_documents') as mock_add_chroma, \
         patch.object(indexer.embeddings, 'embed_batch', new_callable=AsyncMock) as mock_embed:

        # Setup website fetcher mock
        mock_site_fetcher = Mock()
        mock_site_fetcher.list_files = AsyncMock(return_value=[
            Mock(url="https://example.com/page1", path="https://example.com/page1"),
            Mock(url="https://example.com/page2", path="https://example.com/page2"),
        ])
        mock_site_fetcher_class.return_value = mock_site_fetcher

        # Setup page fetcher mock
        mock_page_fetcher = Mock()
        mock_page_fetcher.fetch_content = AsyncMock(return_value="Page content")
        mock_page_fetcher_class.return_value = mock_page_fetcher

        mock_embed.return_value = [[0.1, 0.2, 0.3]]

        source = Source(
            id="web_site:example.com",
            type=SourceType.WEB_SITE,
            url="https://example.com",
            status=SourceStatus.PENDING
        )

        await indexer.index_source(source)
        assert mock_add_chroma.called


@pytest.mark.asyncio
async def test_index_source_updates_status(indexer):
    """Test that source status is updated during indexing"""
    with patch('mcp_server.indexer.WebPageFetcher') as mock_fetcher_class, \
         patch.object(indexer.chroma, 'add_documents') as mock_add_chroma, \
         patch.object(indexer.embeddings, 'embed_batch', new_callable=AsyncMock) as mock_embed:

        mock_fetcher = Mock()
        mock_fetcher.fetch_content = AsyncMock(return_value="Test content")
        mock_fetcher_class.return_value = mock_fetcher

        mock_embed.return_value = [[0.1, 0.2, 0.3]]

        source = Source(
            id="web:test.com",
            type=SourceType.WEB_PAGE,
            url="https://test.com",
            status=SourceStatus.PENDING
        )

        await indexer.index_source(source)

        # Should be called twice: once for indexing, once for ready
        assert indexer.storage.update_source_status.call_count == 2


@pytest.mark.asyncio
async def test_index_source_handles_error(indexer):
    """Test that source status is updated to error on failure"""
    source = Source(
        id="web:test.com",
        type=SourceType.WEB_PAGE,
        url="https://test.com",
        status=SourceStatus.PENDING
    )

    with patch('mcp_server.indexer.WebPageFetcher') as mock_fetcher_class:
        mock_fetcher = Mock()
        mock_fetcher.fetch_content = AsyncMock(
            side_effect=Exception("Network error")
        )
        mock_fetcher_class.return_value = mock_fetcher

        with pytest.raises(Exception):
            await indexer.index_source(source)

        # Should be called with error status (once for indexing, once for error)
        assert indexer.storage.update_source_status.call_count == 2
        # Last call should have error status
        last_call = indexer.storage.update_source_status.call_args_list[-1]
        assert last_call[0][1] == SourceStatus.ERROR


@pytest.mark.asyncio
async def test_index_source_unknown_type(indexer):
    """Test that unknown source type raises ValueError"""
    source = Source(
        id="unknown:source",
        type=SourceType.LOCAL,  # Not supported
        url="file:///some/path",
        status=SourceStatus.PENDING
    )

    with pytest.raises(ValueError, match="Unknown source type"):
        await indexer.index_source(source)


@pytest.mark.asyncio
async def test_store_chunks_empty_list(indexer):
    """Test that _store_chunks handles empty chunks gracefully"""
    # Mock chroma.add_documents to track if it was called
    indexer.chroma.add_documents = Mock()

    await indexer._store_chunks("source_id", "file_path", [])

    # Should not raise and should not call chroma
    assert not indexer.chroma.add_documents.called


@pytest.mark.asyncio
async def test_store_chunks_with_content(indexer):
    """Test that _store_chunks generates embeddings and stores chunks"""
    from mcp_server.chunker import ChunkResult

    with patch.object(indexer.embeddings, 'embed_batch', new_callable=AsyncMock) as mock_embed, \
         patch.object(indexer.chroma, 'add_documents') as mock_add_chroma:

        mock_embed.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]

        chunks = [
            ChunkResult(text="Chunk 1 content", metadata={}),
            ChunkResult(text="Chunk 2 content", metadata={}),
        ]

        await indexer._store_chunks("source_id", "file_path.md", chunks)

        assert mock_embed.called
        assert mock_add_chroma.called