"""Indexer orchestrates the complete indexing pipeline."""
from typing import List, Optional
from mcp_server.config import Config
from mcp_server.models import Source, Document, Chunk, SourceType, SourceStatus
from mcp_server.storage import Storage
from mcp_server.chroma_client import ChromaClient
from mcp_server.embeddings import OllamaEmbeddings
from mcp_server.chunker import Chunker, ChunkResult
from mcp_server.sources.github_git import GitHubRepoCloner
from mcp_server.sources.web import WebPageFetcher, WebSiteFetcher


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
                SourceStatus.INDEXING
            )

            # Fetch content based on source type
            if source.type == SourceType.GITHUB_REPO:
                await self._index_github_repo(source)
            elif source.type == SourceType.GITHUB_FILE:
                await self._index_github_file(source)
            elif source.type == SourceType.WEB_PAGE:
                await self._index_web_page(source)
            elif source.type == SourceType.WEB_SITE:
                await self._index_web_site(source)
            else:
                raise ValueError(f"Unknown source type: {source.type}")

            # Update source status
            await self.storage.update_source_status(
                source.id,
                SourceStatus.READY
            )

        except Exception as e:
            await self.storage.update_source_status(
                source.id,
                SourceStatus.ERROR,
                error_message=str(e)
            )
            raise

    async def _index_github_repo(self, source: Source):
        """Index GitHub repository using git clone"""
        # Get config or use defaults
        config = source.config or {}

        cloner = GitHubRepoCloner(
            repo_url=source.url,
            branch=config.get('branch', 'main'),
            include=config.get('include'),
            exclude=config.get('exclude'),
            max_file_size_mb=self.config.github.max_file_size_mb
        )

        try:
            files = await cloner.list_files()

            # Note: No file limit - language-specific excludes handle large repos efficiently

            for file_info in files:
                # File content is already loaded
                content = file_info.content or await file_info.download()

                # Create document record
                import hashlib
                content_hash = hashlib.sha256(content.encode()).hexdigest()

                document = Document(
                    id=f"{source.id}:{file_info.path}",
                    source_id=source.id,
                    file_path=file_info.path,
                    content_hash=content_hash,
                    chunk_count=0,
                    indexed_at=None
                )

                # Add to storage
                await self.storage.add_document(document)

                # Chunk content
                chunks = self.chunker.chunk(content, file_info.path)

                # Generate embeddings and store
                await self._store_chunks(source.id, file_info.path, chunks)

        finally:
            cloner.cleanup()

    async def _index_github_file(self, source: Source):
        """Index single GitHub file"""
        fetcher = GitHubRepoFetcher(source.url, self.config.github)

        try:
            files = await fetcher.list_files()

            if not files:
                raise ValueError(f"No files found for {source.url}")

            file_info = files[0]
            content = await file_info.download()

            document = Document(
                id=f"{source.id}:{file_info.path}",
                source_id=source.id,
                file_path=file_info.path,
                content_hash=file_info.sha,
                chunk_count=0,
                indexed_at=None
            )

            await self.storage.add_document(document)

            chunks = self.chunker.chunk(content, file_info.path)
            await self._store_chunks(source.id, file_info.path, chunks)

        finally:
            fetcher.close()

    async def _index_web_page(self, source: Source):
        """Index single web page"""
        fetcher = WebPageFetcher(source.url, self.config.web)

        # Fetch content
        content = await fetcher.fetch_content()

        # Create document
        document = Document(
            id=f"{source.id}:{source.url}",
            source_id=source.id,
            file_path=source.url,
            content_hash="",
            chunk_count=0,
            indexed_at=None
        )

        await self.storage.add_document(document)

        # Chunk and store
        chunks = self.chunker.chunk(content, source.url)
        await self._store_chunks(source.id, source.url, chunks)

    async def _index_web_site(self, source: Source):
        """Index entire website via sitemap"""
        fetcher = WebSiteFetcher(source.url, self.config.web)

        # Get all URLs from sitemap
        files = await fetcher.list_files()

        # Index each page
        for file_info in files:
            page_fetcher = WebPageFetcher(file_info.url, self.config.web)
            content = await page_fetcher.fetch_content()

            document = Document(
                id=f"{source.id}:{file_info.url}",
                source_id=source.id,
                file_path=file_info.url,
                content_hash="",
                chunk_count=0,
                indexed_at=None
            )

            await self.storage.add_document(document)

            chunks = self.chunker.chunk(content, file_info.url)
            await self._store_chunks(source.id, file_info.url, chunks)

    async def _store_chunks(
        self,
        source_id: str,
        file_path: str,
        chunks: List[ChunkResult]
    ):
        """Generate embeddings and store chunks in Chroma"""
        if not chunks:
            return

        # Filter out empty chunks
        chunks = [c for c in chunks if c.text and c.text.strip()]
        if not chunks:
            return

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