"""FastMCP server for Knowledge Base integration with Claude Code."""
import os
from pathlib import Path
from typing import Optional, List
import asyncio
from fastmcp import FastMCP
from mcp_server.config import Config
from mcp_server.storage import Storage
from mcp_server.indexer import Indexer
from mcp_server.retriever import Retriever
from mcp_server.models import Source, SourceType


def create_server() -> FastMCP:
    """Create and configure MCP server."""
    # Initialize config
    config_path = os.getenv("KNOWLEDGE_BASE_CONFIG", "~/.config/knowledge-base/config.json")
    config = Config.load_from_file(Path(config_path).expanduser())

    # Initialize components (storage will be initialized lazily on first use)
    storage = Storage(config.chroma.persist_directory_expanded / "storage.db")
    indexer = Indexer(config)
    retriever = Retriever(config)

    # Track if storage is initialized and background tasks
    _initialized = {"storage": False, "indexer": False}
    _background_tasks = set()

    async def ensure_initialized():
        """Ensure storage and indexer are initialized"""
        if not _initialized["storage"]:
            await storage.init()
            _initialized["storage"] = True
        if not _initialized["indexer"]:
            await indexer.initialize()
            _initialized["indexer"] = True

    def start_background_task(coro):
        """Start a background task and track it"""
        task = asyncio.create_task(coro)
        _background_tasks.add(task)
        task.add_done_callback(_background_tasks.discard)
        return task

    mcp = FastMCP("knowledge-base")

    @mcp.tool()
    async def kb_add_repo(
        repo_url: str,
        branch: str = "main",
        include: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None
    ) -> str:
        """
        Add a GitHub repository to the knowledge base.

        Args:
            repo_url: GitHub repository URL (owner/repo or full URL)
            branch: Git branch to index (default: main)
            include: File patterns to include (default: common code and docs)
            exclude: File patterns to exclude (default: node_modules, dist, etc)

        Returns:
            Status message
        """
        await ensure_initialized()

        # Parse repo URL to create source ID
        if repo_url.startswith("http"):
            parts = repo_url.rstrip("/").split("/")
            source_id = f"github:{parts[-2]}/{parts[-1]}"
        else:
            source_id = f"github:{repo_url}"

        # Check if source already exists
        existing = await storage.get_source(source_id)
        if existing:
            return f"Repository {repo_url} already exists in knowledge base"

        # Create source
        source = Source(
            id=source_id,
            type=SourceType.GITHUB_REPO,
            url=repo_url,
            name=repo_url,
            config={
                "branch": branch,
                "include": include or [],
                "exclude": exclude or []
            }
        )

        await storage.add_source(source)

        # Start indexing in background
        start_background_task(indexer.index_source(source))

        return f"Added {repo_url} to knowledge base. Indexing started in background."

    @mcp.tool()
    async def kb_add_url(url: str) -> str:
        """
        Add a single web page to the knowledge base.

        Args:
            url: Web page URL

        Returns:
            Status message
        """
        await ensure_initialized()
        from urllib.parse import urlparse

        # Create source ID from URL
        parsed = urlparse(url)
        source_id = f"web:{parsed.netloc}{parsed.path}"

        existing = await storage.get_source(source_id)
        if existing:
            return f"URL {url} already exists in knowledge base"

        source = Source(
            id=source_id,
            type=SourceType.WEB_PAGE,
            url=url,
            name=url
        )

        await storage.add_source(source)
        start_background_task(indexer.index_source(source))

        return f"Added {url} to knowledge base. Indexing started in background."

    @mcp.tool()
    async def kb_add_site(base_url: str, max_pages: Optional[int] = None) -> str:
        """
        Add an entire website (via sitemap) to the knowledge base.

        Args:
            base_url: Website base URL
            max_pages: Maximum pages to index (default: from config)

        Returns:
            Status message
        """
        await ensure_initialized()
        from urllib.parse import urlparse

        parsed = urlparse(base_url)
        source_id = f"site:{parsed.netloc}"

        existing = await storage.get_source(source_id)
        if existing:
            return f"Website {base_url} already exists in knowledge base"

        source = Source(
            id=source_id,
            type=SourceType.WEB_SITE,
            url=base_url,
            name=base_url,
            config={"max_pages": max_pages} if max_pages else {}
        )

        await storage.add_source(source)
        start_background_task(indexer.index_source(source))

        return f"Added {base_url} to knowledge base. Indexing started in background."

    @mcp.tool()
    async def kb_search(
        query: str,
        n_results: int = 5,
        source_filter: Optional[str] = None
    ) -> str:
        """
        Search the knowledge base.

        Args:
            query: Natural language search query
            n_results: Maximum number of results (default: 5)
            source_filter: Filter by source type (github, web_page, web_site)

        Returns:
            Formatted search results
        """
        await ensure_initialized()
        results = await retriever.search(query, n_results, source_filter)
        return retriever.format_results(results)

    @mcp.tool()
    async def kb_list(source_type: Optional[str] = None) -> str:
        """
        List all sources in the knowledge base.

        Args:
            source_type: Filter by source type (github, web_page, web_site)

        Returns:
            Formatted list of sources
        """
        await ensure_initialized()
        sources = await storage.list_sources()

        if source_type:
            sources = [s for s in sources if s.type.value == source_type]

        if not sources:
            return "No sources found in knowledge base"

        output = [f"Knowledge Base Sources ({len(sources)}):\n"]
        for source in sources:
            output.append(f"- {source.id}")
            output.append(f"  Type: {source.type.value}")
            output.append(f"  URL: {source.url}")
            output.append(f"  Status: {source.status.value}")
            if source.last_indexed_at:
                output.append(f"  Indexed: {source.last_indexed_at.isoformat()}")
            if source.status.value == "error" and source.error_message:
                output.append(f"  Error: {source.error_message}")
            output.append("")

        return "\n".join(output)

    @mcp.tool()
    async def kb_delete(source_id: str) -> str:
        """
        Delete a source from the knowledge base.

        Args:
            source_id: Source ID to delete

        Returns:
            Status message
        """
        await ensure_initialized()
        source = await storage.get_source(source_id)
        if not source:
            return f"Source {source_id} not found"

        await storage.delete_source(source_id)

        return f"Deleted {source_id} from knowledge base"

    @mcp.tool()
    async def kb_status() -> str:
        """
        Show knowledge base statistics and status.

        Returns:
            Formatted status information
        """
        await ensure_initialized()
        sources = await storage.list_sources()
        total_sources = len(sources)
        indexed_sources = len([s for s in sources if s.status.value == "ready"])
        pending_sources = len([s for s in sources if s.status.value == "pending"])
        indexing_sources = len([s for s in sources if s.status.value == "indexing"])
        failed_sources = len([s for s in sources if s.status.value == "error"])

        total_docs = await storage.get_document_count()
        total_chunks = indexer.chroma.count()

        output = [
            "Knowledge Base Status:",
            "",
            "Sources:",
            f"  Total: {total_sources}",
            f"  Indexed: {indexed_sources}",
            f"  Indexing: {indexing_sources}",
            f"  Pending: {pending_sources}",
            f"  Failed: {failed_sources}",
            "",
            f"Documents: {total_docs}",
            f"Chunks: {total_chunks}",
            "",
            f"Storage: {config.chroma.persist_directory_expanded}",
            f"Embedding Model: {config.ollama.model}",
        ]

        return "\n".join(output)

    return mcp


# Create server instance only if config exists or defaults work
try:
    server = create_server()
except Exception:
    server = None

if __name__ == "__main__":
    if server:
        server.run()
    else:
        print("Failed to create server. Please check configuration.")