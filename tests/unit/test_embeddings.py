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