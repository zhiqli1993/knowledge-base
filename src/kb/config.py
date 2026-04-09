from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
import json

DEFAULT_CONFIG_PATH = Path("~/.kb/config.json").expanduser()
LEGACY_CONFIG_PATH = Path("~/.config/knowledge-base/config.json").expanduser()


def resolve_config_path(path_override: Optional[str] = None) -> Path:
    """Resolve the preferred config path with backward compatibility."""
    if path_override:
        return Path(path_override).expanduser()
    if DEFAULT_CONFIG_PATH.exists():
        return DEFAULT_CONFIG_PATH
    if LEGACY_CONFIG_PATH.exists():
        return LEGACY_CONFIG_PATH
    return DEFAULT_CONFIG_PATH


class ChromaConfig(BaseModel):
    host: str = "localhost"
    port: int = 8000
    collection_name: str = "knowledge_base"
    persist_directory: str = "~/.claude/knowledge-base/chroma_db"

    @property
    def persist_directory_expanded(self) -> Path:
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


class LocalConfig(BaseModel):
    allowed_paths: List[str] = Field(default_factory=list)
    allow_unrestricted_paths: bool = False

    @property
    def allowed_paths_expanded(self) -> List[Path]:
        return [Path(path).expanduser().resolve() for path in self.allowed_paths]


class ServiceConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8864
    base_url: Optional[str] = None
    timeout_seconds: int = 30

    @property
    def local_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    @property
    def effective_base_url(self) -> str:
        return self.base_url or self.local_url


class Config(BaseModel):
    chroma: ChromaConfig = Field(default_factory=ChromaConfig)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    github: GitHubConfig = Field(default_factory=GitHubConfig)
    web: WebConfig = Field(default_factory=WebConfig)
    local: LocalConfig = Field(default_factory=LocalConfig)
    indexing: IndexingConfig = Field(default_factory=IndexingConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    service: ServiceConfig = Field(default_factory=ServiceConfig)

    @classmethod
    def load_default(cls) -> "Config":
        return cls()

    @classmethod
    def load_from_file(cls, path: Path) -> "Config":
        resolved_path = path.resolve()
        if not resolved_path.exists():
            return cls()
        try:
            with open(resolved_path, encoding='utf-8') as f:
                data = json.load(f)
        except (IOError, OSError) as e:
            raise RuntimeError(f"Failed to load config from {resolved_path}: {e}")
        return cls(**data)

    def validate(self) -> bool:
        return True

    def save_to_file(self, path: Path):
        resolved_path = path.resolve()
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(resolved_path, 'w', encoding='utf-8') as f:
                json.dump(self.model_dump(exclude_none=True), f, indent=2)
        except (IOError, OSError) as e:
            raise RuntimeError(f"Failed to save config to {resolved_path}: {e}")
