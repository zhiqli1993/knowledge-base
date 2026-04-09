"""Indexer orchestrates the complete indexing pipeline."""
import asyncio
import hashlib
from pathlib import Path
from typing import List, Tuple

from kb.config import Config
from kb.core.local_access import get_allowed_roots
from kb.core.models import Source, Document, Chunk, SourceType, SourceStatus, utcnow
from kb.core.storage import Storage
from kb.core.chroma_client import ChromaClient
from kb.core.embeddings import OllamaEmbeddings
from kb.core.chunker import Chunker, ChunkResult
from kb.sources.github_git import GitHubRepoCloner as GitHubRepoFetcher
from kb.sources.github import GitHubRepoFetcher as GitHubFileFetcher
from kb.sources.local import LocalFileCollector
from kb.sources.web import WebPageFetcher, WebSiteFetcher


class Indexer:
    """Orchestrates the complete indexing pipeline."""

    def __init__(self, config: Config):
        self.config = config
        self.storage = Storage(config.chroma.persist_directory_expanded / "storage.db")
        self.chroma = ChromaClient(config.chroma)
        self.embeddings = OllamaEmbeddings(config.ollama)
        self.chunker = Chunker(
            chunk_size=config.indexing.chunk_size,
            chunk_overlap=config.indexing.chunk_overlap
        )

    async def initialize(self):
        """Initialize storage"""
        await self.storage.init()

    async def index_source(self, source: Source):
        """Index a single source"""
        try:
            # Update source status
            await self.storage.update_source_status(
                source.id,
                SourceStatus.INDEXING,
            )
            await self.storage.update_source_progress(
                source.id,
                phase="starting",
                message="Preparing source for indexing",
                total=0,
                processed=0,
                document_count=0,
                chunk_count=0,
            )

            # Fetch content based on source type
            if source.type == SourceType.GITHUB_REPO:
                document_count, chunk_count = await self._index_github_repo(source)
            elif source.type == SourceType.GITHUB_FILE:
                document_count, chunk_count = await self._index_github_file(source)
            elif source.type == SourceType.WEB_PAGE:
                document_count, chunk_count = await self._index_web_page(source)
            elif source.type == SourceType.WEB_SITE:
                document_count, chunk_count = await self._index_web_site(source)
            elif source.type == SourceType.LOCAL:
                document_count, chunk_count = await self._index_local_source(source)
            else:
                raise ValueError(f"Unknown source type: {source.type}")

            # Update source status
            await self._ensure_source_exists(source.id)
            await self.storage.update_source_status(
                source.id,
                SourceStatus.READY,
                last_indexed_at=utcnow(),
                document_count=document_count,
                chunk_count=chunk_count,
            )
            await self.storage.update_source_progress(
                source.id,
                phase="completed",
                message="Indexing completed",
                total=document_count,
                processed=document_count,
                document_count=document_count,
                chunk_count=chunk_count,
            )

        except Exception as e:
            await self.storage.update_source_status(
                source.id,
                SourceStatus.ERROR,
                error_message=str(e),
            )
            await self.storage.update_source_progress(
                source.id,
                phase="error",
                message=str(e),
            )
            raise

    async def _index_github_repo(self, source: Source) -> Tuple[int, int]:
        """Index GitHub repository using git clone"""
        # Get config or use defaults
        config = source.config or {}
        branch = config.get('branch')
        if not branch:
            branch = await asyncio.to_thread(GitHubRepoFetcher.detect_default_branch, source.url)
            await self.storage.update_source_progress(
                source.id,
                phase="starting",
                message=f"Detected default branch {branch}",
                total=0,
                processed=0,
                document_count=0,
                chunk_count=0,
            )

        cloner = GitHubRepoFetcher(
            repo_url=source.url,
            branch=branch,
            include=config.get('include'),
            exclude=config.get('exclude'),
            max_file_size_mb=self.config.github.max_file_size_mb
        )

        document_count = 0
        chunk_count = 0

        try:
            files = await cloner.list_files()
            await self.storage.update_source_progress(
                source.id,
                phase="fetching",
                message="Fetched repository file list",
                total=len(files),
                processed=0,
                document_count=0,
                chunk_count=0,
            )

            # Note: No file limit - language-specific excludes handle large repos efficiently

            for file_info in files:
                # File content is already loaded
                content = (
                    file_info.content
                    if isinstance(file_info.content, str)
                    else await file_info.download()
                )
                chunk_count += await self._store_document_content(
                    source,
                    file_path=file_info.path,
                    content=content,
                    content_hash=self._hash_content(content),
                )
                document_count += 1
                await self.storage.update_source_progress(
                    source.id,
                    phase="indexing",
                    message=f"Indexed {file_info.path}",
                    total=len(files),
                    processed=document_count,
                    document_count=document_count,
                    chunk_count=chunk_count,
                )

        finally:
            cloner.cleanup()

        return document_count, chunk_count

    async def _index_github_file(self, source: Source) -> Tuple[int, int]:
        """Index single GitHub file"""
        fetcher = GitHubFileFetcher(source.url, self.config.github)

        try:
            files = await fetcher.list_files()

            if not files:
                raise ValueError(f"No files found for {source.url}")

            file_info = files[0]
            content = await file_info.download()
            chunk_count = await self._store_document_content(
                source,
                file_path=file_info.path,
                content=content,
                content_hash=file_info.sha or self._hash_content(content),
            )
            await self.storage.update_source_progress(
                source.id,
                phase="indexing",
                message=f"Indexed {file_info.path}",
                total=1,
                processed=1,
                document_count=1,
                chunk_count=chunk_count,
            )

        finally:
            fetcher.close()

        return 1, chunk_count

    async def _index_web_page(self, source: Source) -> Tuple[int, int]:
        """Index single web page"""
        fetcher = WebPageFetcher(source.url, self.config.web)

        # Fetch content
        content = await fetcher.fetch_content()
        chunk_count = await self._store_document_content(
            source,
            file_path=source.url,
            content=content,
            content_hash=self._hash_content(content),
        )
        await self.storage.update_source_progress(
            source.id,
            phase="indexing",
            message=f"Indexed {source.url}",
            total=1,
            processed=1,
            document_count=1,
            chunk_count=chunk_count,
        )
        return 1, chunk_count

    async def _index_web_site(self, source: Source) -> Tuple[int, int]:
        """Index entire website via sitemap"""
        fetcher = WebSiteFetcher(source.url, self.config.web)

        # Get all URLs from sitemap
        files = await fetcher.list_files()
        await self.storage.update_source_progress(
            source.id,
            phase="fetching",
            message="Fetched sitemap URLs",
            total=len(files),
            processed=0,
            document_count=0,
            chunk_count=0,
        )

        document_count = 0
        chunk_count = 0

        # Index each page
        for file_info in files:
            page_fetcher = WebPageFetcher(file_info.url, self.config.web)
            content = await page_fetcher.fetch_content()
            chunk_count += await self._store_document_content(
                source,
                file_path=file_info.url,
                content=content,
                content_hash=self._hash_content(content),
            )
            document_count += 1
            await self.storage.update_source_progress(
                source.id,
                phase="indexing",
                message=f"Indexed {file_info.url}",
                total=len(files),
                processed=document_count,
                document_count=document_count,
                chunk_count=chunk_count,
            )

        return document_count, chunk_count

    async def _index_local_source(self, source: Source) -> Tuple[int, int]:
        """Index a local file or directory."""
        config = source.config or {}
        include = config.get("include") or self.config.indexing.default_includes
        exclude = config.get("exclude") or self.config.indexing.default_excludes

        collector = LocalFileCollector(
            source_path=source.url,
            include=include,
            exclude=exclude,
            max_file_size_mb=self.config.github.max_file_size_mb,
            allowed_roots=get_allowed_roots(self.config.local, fallback_root=Path.cwd()),
            allow_unrestricted=self.config.local.allow_unrestricted_paths,
        )
        files = await collector.list_files()
        if not files:
            raise ValueError(f"No readable files found in {source.url}")
        await self.storage.update_source_progress(
            source.id,
            phase="fetching",
            message="Collected local files",
            total=len(files),
            processed=0,
            document_count=0,
            chunk_count=0,
        )

        document_count = 0
        chunk_count = 0
        for file_info in files:
            content = (
                file_info.content
                if isinstance(file_info.content, str)
                else await file_info.download()
            )
            chunk_count += await self._store_document_content(
                source,
                file_path=file_info.path,
                content=content,
                content_hash=self._hash_content(content),
            )
            document_count += 1
            await self.storage.update_source_progress(
                source.id,
                phase="indexing",
                message=f"Indexed {file_info.path}",
                total=len(files),
                processed=document_count,
                document_count=document_count,
                chunk_count=chunk_count,
            )

        return document_count, chunk_count

    async def _store_document_content(
        self,
        source: Source,
        file_path: str,
        content: str,
        content_hash: str,
    ) -> int:
        """Store document metadata and chunked content."""
        await self._ensure_source_exists(source.id)
        document_id = f"{source.id}:{file_path}"
        document = Document(
            id=document_id,
            source_id=source.id,
            file_path=file_path,
            content_hash=content_hash,
            chunk_count=0,
            indexed_at=None,
        )

        await self.storage.add_document(document)
        chunks = self.chunker.chunk(content, file_path)
        stored_chunk_count = await self._store_chunks(source.id, file_path, chunks)
        await self.storage.update_document_indexing(
            document_id=document_id,
            chunk_count=stored_chunk_count,
            indexed_at=utcnow(),
        )
        return stored_chunk_count

    async def _store_chunks(
        self,
        source_id: str,
        file_path: str,
        chunks: List[ChunkResult]
    ) -> int:
        """Generate embeddings and store chunks in Chroma"""
        if not chunks:
            return 0

        # Filter out empty chunks
        chunks = [c for c in chunks if c.text and c.text.strip()]
        if not chunks:
            return 0

        # Prepare chunk data
        chunk_objs = [
            Chunk(
                source_id=source_id,
                file_path=file_path,
                chunk_index=i,
                text=chunk.text,
                metadata=chunk.metadata
            )
            for i, chunk in enumerate(chunks)
        ]

        # Generate embeddings in batch
        texts = [c.text for c in chunk_objs]
        embeddings = await self.embeddings.embed_batch(texts)

        # Add to Chroma
        ids = [chunk.id for chunk in chunk_objs]
        documents = texts
        metadatas = [
            {
                **chunk.metadata,
                "source_id": chunk.source_id,
                "file_path": chunk.file_path,
                "chunk_index": chunk.chunk_index
            }
            for chunk in chunk_objs
        ]

        self.chroma.add_documents(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )
        return len(chunk_objs)

    @staticmethod
    def _hash_content(content: str) -> str:
        """Create a stable content hash for stored documents."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    async def _ensure_source_exists(self, source_id: str):
        """Abort indexing if the source was removed while processing."""
        source = await self.storage.get_source(source_id)
        if source is None:
            raise RuntimeError(f"Source {source_id} was deleted during indexing")
