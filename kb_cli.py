#!/usr/bin/env python3
"""
Knowledge Base CLI - Direct interface to test MCP server tools
"""
import asyncio
import sys
from pathlib import Path

from mcp_server.config import Config
from mcp_server.storage import Storage
from mcp_server.indexer import Indexer
from mcp_server.retriever import Retriever
from mcp_server.models import Source, SourceType, SourceStatus


class KnowledgeBaseCLI:
    def __init__(self):
        config_path = Path("~/.config/knowledge-base/config.json").expanduser()
        self.config = Config.load_from_file(config_path) if config_path.exists() else Config.load_default()
        self.storage = Storage(self.config.chroma.persist_directory_expanded / "storage.db")
        self.indexer = Indexer(self.config)
        self.retriever = Retriever(self.config)
        self.initialized = False

    async def ensure_initialized(self):
        if not self.initialized:
            await self.storage.init()
            await self.indexer.initialize()
            self.initialized = True

    async def status(self):
        """Show knowledge base status"""
        await self.ensure_initialized()

        sources = await self.storage.list_sources()

        print("=" * 60)
        print("  Knowledge Base Status")
        print("=" * 60)
        print()
        print(f"Sources:")
        print(f"  Total: {len(sources)}")
        print(f"  Indexed: {len([s for s in sources if s.status == SourceStatus.READY])}")
        print(f"  Pending: {len([s for s in sources if s.status == SourceStatus.PENDING])}")
        print(f"  Indexing: {len([s for s in sources if s.status == SourceStatus.INDEXING])}")
        print(f"  Failed: {len([s for s in sources if s.status == SourceStatus.ERROR])}")
        print()
        print(f"Storage: {self.config.chroma.persist_directory_expanded}")
        print(f"Embedding Model: {self.config.ollama.model}")
        print()

    async def list_sources(self, source_type=None):
        """List all sources"""
        await self.ensure_initialized()

        sources = await self.storage.list_sources()

        if source_type:
            sources = [s for s in sources if s.type.value == source_type]

        if not sources:
            print("No sources found")
            return

        print(f"\nKnowledge Base Sources ({len(sources)}):\n")
        for source in sources:
            print(f"- {source.id}")
            print(f"  Type: {source.type.value}")
            print(f"  URL: {source.url}")
            print(f"  Status: {source.status.value}")
            if hasattr(source, 'indexed_at') and source.indexed_at:
                print(f"  Indexed: {source.indexed_at}")
            print()

    async def add_url(self, url):
        """Add a web page"""
        await self.ensure_initialized()

        source_id = f"web:{url.replace('https://', '').replace('http://', '')}"

        existing = await self.storage.get_source(source_id)
        if existing:
            print(f"URL {url} already exists in knowledge base")
            return

        source = Source(
            id=source_id,
            type=SourceType.WEB_PAGE,
            url=url,
            status=SourceStatus.PENDING
        )

        await self.storage.add_source(source)
        print(f"Added {url} to knowledge base. Starting indexing...")

        try:
            await self.indexer.index_source(source)
            print(f"✅ Indexing completed successfully")
        except Exception as e:
            print(f"❌ Indexing failed: {e}")

    async def add_repo(self, repo_url, branch="main"):
        """Add a GitHub repository"""
        await self.ensure_initialized()

        if repo_url.startswith("http"):
            parts = repo_url.rstrip("/").split("/")
            source_id = f"github:{parts[-2]}/{parts[-1]}"
        else:
            source_id = f"github:{repo_url}"

        existing = await self.storage.get_source(source_id)
        if existing:
            print(f"Repository {repo_url} already exists in knowledge base")
            return

        source = Source(
            id=source_id,
            type=SourceType.GITHUB_REPO,
            url=repo_url if repo_url.startswith("http") else f"https://github.com/{repo_url}",
            status=SourceStatus.PENDING,
            config={"branch": branch}
        )

        await self.storage.add_source(source)
        print(f"Added {repo_url} to knowledge base. Starting indexing...")

        try:
            await self.indexer.index_source(source)
            print(f"✅ Indexing completed successfully")
        except Exception as e:
            print(f"❌ Indexing failed: {e}")

    async def search(self, query, n_results=5):
        """Search knowledge base"""
        await self.ensure_initialized()

        print(f"\n🔍 Searching for: '{query}'\n")

        results = await self.retriever.search(query, n_results=n_results)

        if not results:
            print("No results found")
            return

        print(f"Found {len(results)} results:\n")
        for i, result in enumerate(results, 1):
            print(f"--- Result {i} (score: {result.score:.3f}) ---")
            print(f"Source: {result.source_id}")
            print(f"File: {result.file_path}")
            print(f"\n{result.text}\n")

    async def delete(self, source_id):
        """Delete a source"""
        await self.ensure_initialized()

        source = await self.storage.get_source(source_id)
        if not source:
            print(f"Source {source_id} not found")
            return

        await self.storage.delete_source(source_id)
        print(f"Deleted {source_id} from knowledge base")


async def main():
    if len(sys.argv) < 2:
        print("Knowledge Base CLI")
        print("\nUsage:")
        print("  kb_cli.py status")
        print("  kb_cli.py list [github|web]")
        print("  kb_cli.py add-url <url>")
        print("  kb_cli.py add-repo <owner/repo> [branch]")
        print("  kb_cli.py search <query>")
        print("  kb_cli.py delete <source-id>")
        return

    cli = KnowledgeBaseCLI()
    command = sys.argv[1]

    try:
        if command == "status":
            await cli.status()
        elif command == "list":
            source_type = sys.argv[2] if len(sys.argv) > 2 else None
            await cli.list_sources(source_type)
        elif command == "add-url":
            if len(sys.argv) < 3:
                print("Usage: kb_cli.py add-url <url>")
                return
            await cli.add_url(sys.argv[2])
        elif command == "add-repo":
            if len(sys.argv) < 3:
                print("Usage: kb_cli.py add-repo <owner/repo> [branch]")
                return
            branch = sys.argv[3] if len(sys.argv) > 3 else "main"
            await cli.add_repo(sys.argv[2], branch)
        elif command == "search":
            if len(sys.argv) < 3:
                print("Usage: kb_cli.py search <query>")
                return
            query = " ".join(sys.argv[2:])
            await cli.search(query)
        elif command == "delete":
            if len(sys.argv) < 3:
                print("Usage: kb_cli.py delete <source-id>")
                return
            await cli.delete(sys.argv[2])
        else:
            print(f"Unknown command: {command}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
