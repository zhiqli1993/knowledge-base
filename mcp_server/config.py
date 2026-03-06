from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
import json
import os

class ChromaConfig(BaseModel):
    host: str = "localhost"
    port: int = 8000
    collection_name: str = "knowledge_base"
    persist_directory: str = "~/.claude/knowledge-base/chroma_db"

    @property
    def persist_directory_expanded(self) -> Path:
        """Return persist_directory with tilde expanded"""
        return Path(self.persist_directory).expanduser()

class OllamaConfig(BaseModel):
    host: str = "localhost"
    port: int = 11434
    model: str = "nomic-embed-text"
    timeout: int = 60

class GitHubConfig(BaseModel):
    token: Optional[str] = Field(default=None, exclude=True)
    max_file_size_mb: int = 5

class WebConfig(BaseModel):
    user_agent: str = "KnowledgeBase/1.0"
    timeout: int = 30
    max_pages_per_site: int = 100

class IndexingConfig(BaseModel):
    chunk_size: int = 1000
    chunk_overlap: int = 200
    batch_size: int = 10
    default_includes: List[str] = Field(default_factory=lambda: [
        "**/*.md", "**/README*", "**/docs/**",
        "**/*.ts", "**/*.py", "**/*.go"
    ])
    default_excludes: List[str] = Field(default_factory=lambda: [
        "**/node_modules/**", "**/.git/**", "**/dist/**",
        "**/build/**", "**/*.test.*", "**/*.spec.*"
    ])

    @field_validator('chunk_size')
    @classmethod
    def validate_chunk_size(cls, v):
        if v <= 0:
            raise ValueError("chunk_size must be positive")
        return v

    @field_validator('chunk_overlap')
    @classmethod
    def validate_chunk_overlap(cls, v, info):
        chunk_size = info.data.get('chunk_size')
        if chunk_size is not None and v >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        return v

class RetrievalConfig(BaseModel):
    default_top_k: int = 5
    similarity_threshold: float = 0.7

class Config(BaseModel):
    chroma: ChromaConfig = Field(default_factory=ChromaConfig)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    github: GitHubConfig = Field(default_factory=GitHubConfig)
    web: WebConfig = Field(default_factory=WebConfig)
    indexing: IndexingConfig = Field(default_factory=IndexingConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)

    @classmethod
    def load_default(cls) -> "Config":
        """Load default configuration"""
        return cls()

    @classmethod
    def load_from_file(cls, path: Path) -> "Config":
        """Load configuration from JSON file"""
        resolved_path = path.resolve()
        try:
            with open(resolved_path) as f:
                data = json.load(f)
        except (IOError, OSError) as e:
            raise RuntimeError(f"Failed to load config from {resolved_path}: {e}")
        return cls(**data)

    def validate(self) -> bool:
        """Validate configuration"""
        # Validation happens on init, this is a no-op check
        return True

    def save_to_file(self, path: Path):
        """Save configuration to JSON file"""
        resolved_path = path.resolve()
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(resolved_path, 'w') as f:
                json.dump(self.model_dump(), f, indent=2)
        except (IOError, OSError) as e:
            raise RuntimeError(f"Failed to save config to {resolved_path}: {e}")