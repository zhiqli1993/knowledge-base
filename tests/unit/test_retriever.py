import pytest
from unittest.mock import Mock, AsyncMock, patch
from mcp_server.retriever import Retriever
from mcp_server.config import Config
from mcp_server.models import SearchResult


@pytest.mark.asyncio
async def test_search_returns_results():
    """Test semantic search returns formatted results"""
    with patch('mcp_server.retriever.ChromaClient') as mock_chroma_class:
        # Mock ChromaClient
        mock_chroma = Mock()
        mock_chroma_class.return_value = mock_chroma

        config = Config()
        retriever = Retriever(config)

        # Mock embeddings and Chroma query
        with patch.object(retriever.embeddings, 'embed', new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [0.1] * 768
            mock_chroma.query.return_value = {
                'ids': [['chunk1', 'chunk2']],
                'documents': [['Content 1', 'Content 2']],
                'metadatas': [[
                    {'source_id': 'github:owner/repo', 'file_path': 'README.md'},
                    {'source_id': 'github:owner/repo', 'file_path': 'docs/guide.md'}
                ]],
                'distances': [[0.2, 0.3]]
            }

            results = await retriever.search("test query", n_results=5)

            assert len(results) == 2
            assert isinstance(results[0], SearchResult)
            assert results[0].text == 'Content 1'
            assert results[0].score > results[1].score  # Lower distance = higher score


@pytest.mark.asyncio
async def test_search_with_source_filter():
    """Test search with source type filtering"""
    with patch('mcp_server.retriever.ChromaClient') as mock_chroma_class:
        mock_chroma = Mock()
        mock_chroma_class.return_value = mock_chroma

        config = Config()
        retriever = Retriever(config)

        with patch.object(retriever.embeddings, 'embed', new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [0.1] * 768
            mock_chroma.query.return_value = {
                'ids': [[]],
                'documents': [[]],
                'metadatas': [[]],
                'distances': [[]]
            }

            await retriever.search("test", source_filter="github")

            # Verify where filter was applied
            call_args = mock_chroma.query.call_args
            assert 'where' in call_args[1]


@pytest.mark.asyncio
async def test_search_empty_results():
    """Test search with no matching results"""
    with patch('mcp_server.retriever.ChromaClient') as mock_chroma_class:
        mock_chroma = Mock()
        mock_chroma_class.return_value = mock_chroma

        config = Config()
        retriever = Retriever(config)

        with patch.object(retriever.embeddings, 'embed', new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [0.1] * 768
            mock_chroma.query.return_value = {
                'ids': [[]],
                'documents': [[]],
                'metadatas': [[]],
                'distances': [[]]
            }

            results = await retriever.search("no match")
            assert results == []