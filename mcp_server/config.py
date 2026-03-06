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

class OllamaConfig(BaseModel):
    host: str = "localhost"
    port: int = 11434
    model: str = "nomic-embed-text"
    timeout: int = 60

class GitHubConfig(BaseModel):
    token: Optional[str] = None
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
        with open(path) as f:
            data = json.load(f)
        return cls(**data)

    def validate(self) -> bool:
        """Validate configuration by re-validating all nested models"""
        # Re-validate each nested config to trigger validators
        self.model_validate(self.model_dump())
        return True

    def save_to_file(self, path: Path):
        """Save configuration to JSON file"""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.model_dump(), f, indent=2)