import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from kb.config import Config
from kb.core.indexer import Indexer
from kb.core.models import Source, SourceStatus, SourceType
from kb.core.retriever import Retriever
from kb.core.storage import Storage
from kb.core.local_access import get_allowed_roots, is_path_allowed


class KBService:
    def __init__(self, config: Config):
        self.config = config
        self.storage = Storage(config.chroma.persist_directory_expanded / "storage.db")
        self.indexer = Indexer(config)
        self.retriever = Retriever(config)
        self._initialized = False
        self._background_tasks: dict[str, asyncio.Task] = {}

    async def initialize(self):
        if not self._initialized:
            await self.storage.init()
            await self.indexer.initialize()
            self._initialized = True

    async def health(self) -> Dict[str, Any]:
        await self.initialize()
        return {"ok": True, "base_url": self.config.service.effective_base_url}

    def _track_task(self, source_id: str, coro) -> None:
        task = asyncio.create_task(coro)

        def _cleanup(done_task: asyncio.Task):
            if self._background_tasks.get(source_id) is done_task:
                self._background_tasks.pop(source_id, None)

        self._background_tasks[source_id] = task
        task.add_done_callback(_cleanup)

    async def _create_source(self, source: Source) -> Dict[str, Any]:
        await self.initialize()
        existing = await self.storage.get_source(source.id)
        if existing:
            raise ValueError(f"Source {source.id} already exists")
        await self.storage.add_source(source)
        self._track_task(source.id, self.indexer.index_source(source))
        return {
            "accepted": True,
            "message": "Indexing started",
            "source": await self._serialize_source(source.id),
        }

    async def add_url(self, url: str) -> Dict[str, Any]:
        parsed = urlparse(url)
        source_id = f"web:{parsed.netloc}{parsed.path}"
        source = Source(id=source_id, type=SourceType.WEB_PAGE, url=url, name=url)
        return await self._create_source(source)

    async def add_site(self, base_url: str, max_pages: Optional[int] = None) -> Dict[str, Any]:
        parsed = urlparse(base_url)
        source_id = f"site:{parsed.netloc}"
        source = Source(
            id=source_id,
            type=SourceType.WEB_SITE,
            url=base_url,
            name=base_url,
            config={"max_pages": max_pages} if max_pages is not None else {},
        )
        return await self._create_source(source)

    async def add_repo(
        self,
        repo_url: str,
        branch: Optional[str] = None,
        include: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        if repo_url.startswith("http"):
            parts = repo_url.rstrip("/").split("/")
            source_id = f"github:{parts[-2]}/{parts[-1]}"
            url = repo_url
        else:
            source_id = f"github:{repo_url}"
            url = f"https://github.com/{repo_url}"
        source = Source(
            id=source_id,
            type=SourceType.GITHUB_REPO,
            url=url,
            name=repo_url,
            config={"branch": branch, "include": include or [], "exclude": exclude or []},
        )
        return await self._create_source(source)

    async def add_local(
        self,
        path: str,
        include: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        resolved_path = Path(path).expanduser().resolve()
        if not resolved_path.exists():
            raise FileNotFoundError(f"Local path {resolved_path} not found")
        allowed_roots = get_allowed_roots(self.config.local, fallback_root=Path.cwd())
        if not is_path_allowed(
            resolved_path,
            allowed_roots,
            self.config.local.allow_unrestricted_paths,
        ):
            roots_display = ", ".join(str(root) for root in allowed_roots) or "<none>"
            raise PermissionError(
                f"Local path {resolved_path} is outside the allowed roots: {roots_display}."
            )
        source = Source(
            id=f"local:{resolved_path}",
            type=SourceType.LOCAL,
            url=str(resolved_path),
            name=resolved_path.name or str(resolved_path),
            config={"include": include or [], "exclude": exclude or []},
        )
        return await self._create_source(source)

    async def list_sources(self, source_type: Optional[str] = None) -> Dict[str, Any]:
        await self.initialize()
        sources = await self.storage.list_sources()
        if source_type:
            sources = [s for s in sources if s.type.value == source_type]
        return {"sources": [self._source_to_dict(source) for source in sources]}

    async def get_source(self, source_id: str) -> Dict[str, Any]:
        await self.initialize()
        source = await self.storage.get_source(source_id)
        if not source:
            raise KeyError(f"Source {source_id} not found")
        return {"source": self._source_to_dict(source)}

    async def get_progress(self, source_id: str) -> Dict[str, Any]:
        return await self.get_source(source_id)

    async def search(
        self,
        query: str,
        n_results: int = 5,
        source_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        await self.initialize()
        results = await self.retriever.search(query, n_results=n_results, source_filter=source_filter)
        return {
            "query": query,
            "results": [result.model_dump(mode='json') for result in results],
        }

    async def delete_source(self, source_id: str) -> Dict[str, Any]:
        await self.initialize()
        source = await self.storage.get_source(source_id)
        if not source:
            raise KeyError(f"Source {source_id} not found")
        task = self._background_tasks.pop(source_id, None)
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self.indexer.chroma.delete_by_source(source_id)
        await self.storage.delete_source(source_id)
        return {"deleted": True, "source_id": source_id}

    async def reindex_source(self, source_id: str) -> Dict[str, Any]:
        await self.initialize()
        source = await self.storage.get_source(source_id)
        if not source:
            raise KeyError(f"Source {source_id} not found")
        self.indexer.chroma.delete_by_source(source_id)
        await self.storage.delete_documents_for_source(source_id)
        await self.storage.update_source_status(
            source_id,
            SourceStatus.PENDING,
            error_message=None,
            document_count=0,
            chunk_count=0,
        )
        await self.storage.update_source_progress(
            source_id,
            phase="queued",
            message="Reindex queued",
            total=0,
            processed=0,
            document_count=0,
            chunk_count=0,
        )
        refreshed = await self.storage.get_source(source_id)
        assert refreshed is not None
        self._track_task(source_id, self.indexer.index_source(refreshed))
        return {
            "accepted": True,
            "message": "Reindex started",
            "source": self._source_to_dict(refreshed),
        }

    async def update_source(self, source_id: str) -> Dict[str, Any]:
        return await self.reindex_source(source_id)

    async def status(self) -> Dict[str, Any]:
        await self.initialize()
        sources = await self.storage.list_sources()
        return {
            "sources": {
                "total": len(sources),
                "indexed": len([s for s in sources if s.status == SourceStatus.READY]),
                "indexing": len([s for s in sources if s.status == SourceStatus.INDEXING]),
                "pending": len([s for s in sources if s.status == SourceStatus.PENDING]),
                "failed": len([s for s in sources if s.status == SourceStatus.ERROR]),
            },
            "documents": await self.storage.get_document_count(),
            "chunks": self.indexer.chroma.count(),
            "storage": str(self.config.chroma.persist_directory_expanded),
            "embedding_model": self.config.ollama.model,
            "service": {
                "base_url": self.config.service.effective_base_url,
                "host": self.config.service.host,
                "port": self.config.service.port,
            },
        }

    async def reindex_all(self) -> Dict[str, Any]:
        await self.initialize()
        sources = await self.storage.list_sources()
        for source in sources:
            await self.reindex_source(source.id)
        return {"accepted": True, "count": len(sources), "message": "Reindex started for all sources"}

    async def update_all(self) -> Dict[str, Any]:
        return await self.reindex_all()

    async def _serialize_source(self, source_id: str) -> Dict[str, Any]:
        source = await self.storage.get_source(source_id)
        if source is None:
            raise KeyError(f"Source {source_id} not found")
        return self._source_to_dict(source)

    @staticmethod
    def _source_to_dict(source: Source) -> Dict[str, Any]:
        return source.model_dump(mode='json')
