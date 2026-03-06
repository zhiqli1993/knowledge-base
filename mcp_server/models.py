from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum

def utcnow() -> datetime:
    """Return current UTC time with timezone info."""
    return datetime.now(timezone.utc)

class SourceType(str, Enum):
    GITHUB_REPO = "github_repo"
    GITHUB_FILE = "github_file"
    WEB_PAGE = "web_page"
    WEB_SITE = "web_site"
    LOCAL = "local"

class SourceStatus(str, Enum):
    PENDING = "pending"
    INDEXING = "indexing"
    READY = "ready"
    ERROR = "error"

class Source(BaseModel):
    id: str
    type: SourceType
    url: str
    name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    status: SourceStatus = SourceStatus.PENDING
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)
    last_indexed_at: Optional[datetime] = None
    document_count: int = 0
    chunk_count: int = 0

class Document(BaseModel):
    id: str
    source_id: str
    file_path: Optional[str] = None
    content_hash: Optional[str] = None
    chunk_count: Optional[int] = None
    indexed_at: Optional[datetime] = None

class Chunk(BaseModel):
    source_id: str
    file_path: str
    chunk_index: int
    text: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None

    @property
    def id(self) -> str:
        """Generate unique chunk ID"""
        return f"{self.source_id}:{self.file_path}:chunk_{self.chunk_index}"

class SearchResult(BaseModel):
    content: str
    metadata: Dict[str, Any]
    score: float
    source: Optional[Source] = None