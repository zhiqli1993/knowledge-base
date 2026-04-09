"""Comprehensive end-to-end integration tests for the complete workflow.

Tests the full pipeline: add source -> index -> search across different source types.
"""
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from kb.config import Config, ChromaConfig
from kb.core.storage import Storage
from kb.core.indexer import Indexer
from kb.core.retriever import Retriever
from kb.core.models import Source, SourceType, SourceStatus


@pytest.fixture
def temp_dir(tmp_path):
    """Create temporary directory for E2E tests"""
    return str(tmp_path)


@pytest.fixture
def config(temp_dir):
    """Create test configuration with temp directories"""
    return Config(
        chroma=ChromaConfig(persist_directory=f"{temp_dir}/chroma_db"),
        ollama__host="localhost",
        ollama__port=11434,
        ollama__model="nomic-embed-text"
    )


@pytest.fixture
def mock_chroma_client():
    """Create a mock ChromaClient"""
    mock = Mock()
    mock.add_documents = Mock()
    mock.query = Mock(return_value={
        'ids': [[]],
        'documents': [[]],
        'metadatas': [[]],
        'distances': [[]]
    })
    mock.count = Mock(return_value=0)
    mock.delete = Mock()
    return mock


@pytest.mark.asyncio
async def test_complete_github_workflow(temp_dir, config, mock_chroma_client):
    """
    E2E test: Add GitHub repo -> Index -> Search

    Workflow:
    1. Create knowledge base with temp storage
    2. Add GitHub repository
    3. Index the repository
    4. Search for content
    5. Verify results
    """
    # Initialize components with Chroma mocked
    storage_path = Path(temp_dir) / "chroma_db" / "storage.db"
    storage = Storage(storage_path)
    await storage.init()

    with patch('kb.core.indexer.ChromaClient', return_value=mock_chroma_client):
        indexer = Indexer(config)
        await indexer.initialize()

        retriever = Retriever(config)

        # Mock GitHub fetcher
        with patch('kb.core.indexer.GitHubRepoFetcher') as mock_fetcher_class, \
             patch.object(indexer.embeddings, 'embed_batch', new_callable=AsyncMock) as mock_embed:

            # Setup mock file
            mock_file = Mock()
            mock_file.path = "README.md"
            mock_file.url = "https://github.com/test/repo/blob/main/README.md"
            mock_file.size = 1024
            mock_file.sha = "abc123"
            mock_file.language = "markdown"
            mock_file.download = AsyncMock(return_value="""
# Test Repository

This is a test repository for the knowledge base system.

## Features

- Feature 1: Content extraction
- Feature 2: Semantic search
- Feature 3: Vector embeddings

## Installation

Install dependencies with pip install.
            """)

            mock_fetcher = Mock()
            mock_fetcher.list_files = AsyncMock(return_value=[mock_file])
            mock_fetcher.close = Mock()
            mock_fetcher_class.return_value = mock_fetcher

            # Return mock embeddings
            mock_embed.return_value = [[0.1] * 768, [0.2] * 768, [0.3] * 768]

            # Step 1: Add source
            source = Source(
                id="github:test/repo",
                type=SourceType.GITHUB_REPO,
                url="https://github.com/test/repo",
                status=SourceStatus.PENDING
            )

            await storage.add_source(source)

            # Verify source was added
            added_source = await storage.get_source("github:test/repo")
            assert added_source is not None
            assert added_source.status == SourceStatus.PENDING

            # Step 2: Index the repository
            await indexer.index_source(source)

            # Verify source status updated
            indexed_source = await storage.get_source("github:test/repo")
            assert indexed_source.status == SourceStatus.READY

            # Verify chunks were stored
            assert mock_chroma_client.add_documents.called

    # Step 3: Search
    with patch('kb.core.retriever.ChromaClient', return_value=mock_chroma_client) as mock_chroma_class:
        retriever = Retriever(config)

        with patch.object(retriever.embeddings, 'embed', new_callable=AsyncMock) as mock_query_embed:

            mock_query_embed.return_value = [0.15] * 768  # Similar to first chunk

            # Mock Chroma query response - must have actual results for metadatas access
            mock_chroma_client.query.return_value = {
                'ids': [['github:test/repo:README.md:chunk_0']],
                'documents': [['This is a test repository for the knowledge base system.']],
                'metadatas': [[{
                    'source_id': 'github:test/repo',
                    'file_path': 'README.md',
                    'chunk_index': 0
                }]],
                'distances': [[0.1]]
            }

            results = await retriever.search("semantic search features", n_results=3)

            # Step 4: Verify results
            assert len(results) > 0
            assert results[0].source_id == "github:test/repo"


@pytest.mark.asyncio
async def test_complete_web_page_workflow(temp_dir, config, mock_chroma_client):
    """
    E2E test: Add web page -> Index -> Search

    Workflow:
    1. Add web page URL
    2. Fetch and index content
    3. Search for content
    4. Verify results
    """
    storage_path = Path(temp_dir) / "chroma_db" / "storage.db"
    storage = Storage(storage_path)
    await storage.init()

    with patch('kb.core.indexer.ChromaClient', return_value=mock_chroma_client):
        indexer = Indexer(config)
        await indexer.initialize()

        # Mock web fetcher
        with patch('kb.core.indexer.WebPageFetcher') as mock_fetcher_class, \
             patch.object(indexer.embeddings, 'embed_batch', new_callable=AsyncMock) as mock_embed:

            mock_fetcher = Mock()
            mock_fetcher.fetch_content = AsyncMock(return_value="""
Python Asyncio Tutorial

Learn about async/await in Python for concurrent programming.

Key concepts:
- Event loop
- Coroutines
- Tasks and futures
- Concurrent execution

Example:
async def main():
    await asyncio.sleep(1)
    print("Done")
            """)

            mock_fetcher_class.return_value = mock_fetcher
            mock_embed.return_value = [[0.1] * 768, [0.2] * 768]

            # Add and index web page
            source = Source(
                id="web:example.com/asyncio-tutorial",
                type=SourceType.WEB_PAGE,
                url="https://example.com/asyncio-tutorial",
                status=SourceStatus.PENDING
            )

            await storage.add_source(source)
            await indexer.index_source(source)

            # Verify indexing
            indexed_source = await storage.get_source("web:example.com/asyncio-tutorial")
            assert indexed_source.status == SourceStatus.READY

    # Search - need to mock Retriever's ChromaClient
    with patch('kb.core.retriever.ChromaClient', return_value=mock_chroma_client):
        retriever = Retriever(config)

        with patch.object(retriever.embeddings, 'embed', new_callable=AsyncMock) as mock_query_embed:

            mock_query_embed.return_value = [0.15] * 768

            mock_chroma_client.query.return_value = {
                'ids': [['web:example.com/asyncio-tutorial:https://example.com/asyncio-tutorial:chunk_0']],
                'documents': [['Learn about async/await in Python for concurrent programming.']],
                'metadatas': [[{
                    'source_id': 'web:example.com/asyncio-tutorial',
                    'file_path': 'https://example.com/asyncio-tutorial',
                    'chunk_index': 0
                }]],
                'distances': [[0.1]]
            }

            results = await retriever.search("async await python", n_results=3)

            assert len(results) > 0
            assert results[0].source_id == "web:example.com/asyncio-tutorial"


@pytest.mark.asyncio
async def test_multiple_sources_with_filtering(temp_dir, config, mock_chroma_client):
    """
    E2E test: Multiple sources with filtering

    Workflow:
    1. Add multiple sources (GitHub + Web)
    2. Index all sources
    3. Search with source filtering
    4. Verify filtering works
    """
    storage_path = Path(temp_dir) / "chroma_db" / "storage.db"
    storage = Storage(storage_path)
    await storage.init()

    with patch('kb.core.indexer.ChromaClient', return_value=mock_chroma_client):
        indexer = Indexer(config)
        await indexer.initialize()

        # Mock both GitHub and web fetchers
        with patch('kb.core.indexer.GitHubRepoFetcher') as mock_gh, \
             patch('kb.core.indexer.WebPageFetcher') as mock_web, \
             patch.object(indexer.embeddings, 'embed_batch', new_callable=AsyncMock) as mock_embed:

            # Setup GitHub mock
            mock_gh_file = Mock()
            mock_gh_file.path = "docs/guide.md"
            mock_gh_file.url = "https://github.com/test/repo/blob/main/docs/guide.md"
            mock_gh_file.size = 500
            mock_gh_file.sha = "xyz789"
            mock_gh_file.language = "markdown"
            mock_gh_file.download = AsyncMock(return_value="# GitHub Guide\n\nLearn Git and GitHub.")

            mock_gh_fetcher = Mock()
            mock_gh_fetcher.list_files = AsyncMock(return_value=[mock_gh_file])
            mock_gh_fetcher.close = Mock()
            mock_gh.return_value = mock_gh_fetcher

            # Setup web mock
            mock_web_fetcher = Mock()
            mock_web_fetcher.fetch_content = AsyncMock(return_value="Web Development Tutorial")
            mock_web.return_value = mock_web_fetcher

            mock_embed.return_value = [[0.1] * 768]

            # Add GitHub source
            github_source = Source(
                id="github:test/repo",
                type=SourceType.GITHUB_REPO,
                url="https://github.com/test/repo",
                status=SourceStatus.PENDING
            )
            await storage.add_source(github_source)
            await indexer.index_source(github_source)

            # Add web source
            web_source = Source(
                id="web:example.com/tutorial",
                type=SourceType.WEB_PAGE,
                url="https://example.com/tutorial",
                status=SourceStatus.PENDING
            )
            await storage.add_source(web_source)
            await indexer.index_source(web_source)

    # Search with GitHub filter
    with patch('kb.core.retriever.ChromaClient', return_value=mock_chroma_client):
        retriever = Retriever(config)

        with patch.object(retriever.embeddings, 'embed', new_callable=AsyncMock) as mock_query:

            mock_query.return_value = [0.1] * 768

            # Mock: GitHub result
            mock_chroma_client.query.return_value = {
                'ids': [['github:test/repo:docs/guide.md:chunk_0']],
                'documents': [['# GitHub Guide\n\nLearn Git and GitHub.']],
                'metadatas': [[{
                    'source_id': 'github:test/repo',
                    'file_path': 'docs/guide.md',
                    'chunk_index': 0
                }]],
                'distances': [[0.1]]
            }

            # Filter by GitHub
            github_results = await retriever.search("guide", source_filter="github")

            # Verify where filter was applied
            call_args = mock_chroma_client.query.call_args
            assert 'where' in call_args[1]
            where_filter = call_args[1]['where']
            # Structure is {"source_id": {"$contains": "github"}}
            assert where_filter.get('source_id', {}).get('$contains') == 'github'
            assert all("github:" in r.source_id for r in github_results)

            # Mock: Web result
            mock_chroma_client.query.return_value = {
                'ids': [['web:example.com/tutorial:https://example.com/tutorial:chunk_0']],
                'documents': [['Web Development Tutorial']],
                'metadatas': [[{
                    'source_id': 'web:example.com/tutorial',
                    'file_path': 'https://example.com/tutorial',
                    'chunk_index': 0
                }]],
                'distances': [[0.2]]
            }

            # Filter by web
            web_results = await retriever.search("tutorial", source_filter="web")
            assert all("web:" in r.source_id for r in web_results)


@pytest.mark.asyncio
async def test_error_handling_workflow(temp_dir, config, mock_chroma_client):
    """
    E2E test: Error handling during indexing

    Workflow:
    1. Add source that will fail
    2. Verify error is captured
    3. Verify source status is updated to 'error'
    """
    storage_path = Path(temp_dir) / "chroma_db" / "storage.db"
    storage = Storage(storage_path)
    await storage.init()

    with patch('kb.core.indexer.ChromaClient', return_value=mock_chroma_client):
        indexer = Indexer(config)
        await indexer.initialize()

        # Mock fetcher that raises error
        with patch('kb.core.indexer.GitHubRepoFetcher') as mock_fetcher_class:
            mock_fetcher = Mock()
            mock_fetcher.list_files = AsyncMock(side_effect=RuntimeError("API rate limit exceeded"))
            mock_fetcher.close = Mock()
            mock_fetcher_class.return_value = mock_fetcher

            source = Source(
                id="github:test/failing-repo",
                type=SourceType.GITHUB_REPO,
                url="https://github.com/test/failing-repo",
                status=SourceStatus.PENDING
            )

            await storage.add_source(source)

            # Try to index - should fail gracefully
            with pytest.raises(RuntimeError):
                await indexer.index_source(source)

            # Verify status updated to error
            failed_source = await storage.get_source("github:test/failing-repo")
            assert failed_source.status == SourceStatus.ERROR
            assert "API rate limit exceeded" in (failed_source.error_message or "")


@pytest.mark.asyncio
async def test_search_with_empty_results(temp_dir, config, mock_chroma_client):
    """Test search returns empty list when no matches found"""
    with patch('kb.core.retriever.ChromaClient', return_value=mock_chroma_client):
        retriever = Retriever(config)

        with patch.object(retriever.embeddings, 'embed', new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [0.1] * 768

            mock_chroma_client.query.return_value = {
                'ids': [[]],
                'documents': [[]],
                'metadatas': [[]],
                'distances': [[]]
            }

            results = await retriever.search("nonexistent query")
            assert results == []


@pytest.mark.asyncio
async def test_search_with_similarity_threshold(temp_dir, config, mock_chroma_client):
    """Test search respects similarity threshold"""
    with patch('kb.core.retriever.ChromaClient', return_value=mock_chroma_client):
        retriever = Retriever(config)

        with patch.object(retriever.embeddings, 'embed', new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [0.1] * 768

            # Mock: High distance (low similarity)
            mock_chroma_client.query.return_value = {
                'ids': [['chunk1']],
                'documents': [['Some content']],
                'metadatas': [[{
                    'source_id': 'test',
                    'file_path': 'test.md',
                    'chunk_index': 0
                }]],
                'distances': [[0.9]]  # High distance = low similarity
            }

            results = await retriever.search("query", n_results=5)

            # Verify score calculation (score = 1 / (1 + distance))
            if results:
                assert results[0].score == pytest.approx(0.526, rel=0.01)  # 1 / (1 + 0.9)


@pytest.mark.asyncio
async def test_index_source_status_transitions(temp_dir, config, mock_chroma_client):
    """Test that source status transitions correctly during indexing"""
    storage_path = Path(temp_dir) / "chroma_db" / "storage.db"
    storage = Storage(storage_path)
    await storage.init()

    with patch('kb.core.indexer.ChromaClient', return_value=mock_chroma_client):
        indexer = Indexer(config)
        await indexer.initialize()

        with patch('kb.core.indexer.WebPageFetcher') as mock_fetcher_class, \
             patch.object(indexer.embeddings, 'embed_batch', new_callable=AsyncMock) as mock_embed:

            mock_fetcher = Mock()
            mock_fetcher.fetch_content = AsyncMock(return_value="Test content for status transitions")
            mock_fetcher_class.return_value = mock_fetcher

            mock_embed.return_value = [[0.1] * 768]

            source = Source(
                id="web:test-status.com",
                type=SourceType.WEB_PAGE,
                url="https://test-status.com",
                status=SourceStatus.PENDING
            )

            await storage.add_source(source)

            # Initially should be pending
            initial_source = await storage.get_source("web:test-status.com")
            assert initial_source.status == SourceStatus.PENDING

            # After indexing
            await indexer.index_source(source)

            # Should be ready
            final_source = await storage.get_source("web:test-status.com")
            assert final_source.status == SourceStatus.READY


@pytest.mark.asyncio
async def test_complete_workflow_with_all_source_types(temp_dir, config, mock_chroma_client):
    """E2E test covering all source types in a single test"""
    storage_path = Path(temp_dir) / "chroma_db" / "storage.db"
    storage = Storage(storage_path)
    await storage.init()

    with patch('kb.core.indexer.ChromaClient', return_value=mock_chroma_client):
        indexer = Indexer(config)
        await indexer.initialize()

        sources_to_test = [
            {
                "id": "github:owner/repo",
                "type": SourceType.GITHUB_REPO,
                "url": "https://github.com/owner/repo",
                "content": "# GitHub Repository\n\nCode and documentation."
            },
            {
                "id": "web:example.com/article",
                "type": SourceType.WEB_PAGE,
                "url": "https://example.com/article",
                "content": "Web page content about technology."
            }
        ]

        for source_data in sources_to_test:
            with patch('kb.core.indexer.WebPageFetcher') if source_data["type"] == SourceType.WEB_PAGE else patch('kb.core.indexer.GitHubRepoFetcher') as mock_fetcher_class, \
                 patch.object(indexer.embeddings, 'embed_batch', new_callable=AsyncMock) as mock_embed:

                mock_fetcher = Mock()

                if source_data["type"] == SourceType.WEB_PAGE:
                    mock_fetcher.fetch_content = AsyncMock(return_value=source_data["content"])
                else:
                    mock_fetcher.list_files = AsyncMock(return_value=[
                        Mock(
                            path="README.md",
                            url=f"{source_data['url']}/blob/main/README.md",
                            size=100,
                            sha="abc123",
                            language="markdown",
                            download=AsyncMock(return_value=source_data["content"])
                        )
                    ])
                    mock_fetcher.close = Mock()

                mock_fetcher_class.return_value = mock_fetcher
                mock_embed.return_value = [[0.1] * 768]

                source = Source(
                    id=source_data["id"],
                    type=source_data["type"],
                    url=source_data["url"],
                    status=SourceStatus.PENDING
                )

                await storage.add_source(source)
                await indexer.index_source(source)

                # Verify indexed
                indexed = await storage.get_source(source_data["id"])
                assert indexed.status == SourceStatus.READY

    # Verify we can search across all sources
    with patch('kb.core.retriever.ChromaClient', return_value=mock_chroma_client):
        retriever = Retriever(config)

        with patch.object(retriever.embeddings, 'embed', new_callable=AsyncMock) as mock_embed:

            mock_embed.return_value = [0.1] * 768
            mock_chroma_client.query.return_value = {
                'ids': [[]],
                'documents': [[]],
                'metadatas': [[]],
                'distances': [[]]
            }

            # Search without filter should query all sources
            await retriever.search("content")

            # No source filter means no 'where' clause
            call_args = mock_chroma_client.query.call_args
            assert call_args[1].get('where') is None

            # Search with github filter
            await retriever.search("github", source_filter="github")
            call_args = mock_chroma_client.query.call_args
            assert 'where' in call_args[1]