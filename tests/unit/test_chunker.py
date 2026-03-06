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
    # Check headers are preserved in metadata
    assert all(chunk.metadata.get("headers") for chunk in chunks)

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