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