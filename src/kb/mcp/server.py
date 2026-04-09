"""FastMCP proxy for the knowledge base web service."""
import os
from typing import List, Optional

from fastmcp import FastMCP

from kb.client.http import KBHttpClient
from kb.config import Config, resolve_config_path
from kb.presenters import format_message, format_search, format_sources, format_status, format_source


def create_server() -> FastMCP:
    config_path = resolve_config_path(os.getenv("KNOWLEDGE_BASE_CONFIG"))
    config = Config.load_from_file(config_path)
    client = KBHttpClient(config)
    mcp = FastMCP("knowledge-base")

    @mcp.tool()
    async def kb_add_repo(repo_url: str, branch: Optional[str] = None, include: Optional[List[str]] = None, exclude: Optional[List[str]] = None) -> str:
        data = await client.add_repo(repo_url, branch, include, exclude)
        return format_message(data["message"]) + "\n\n" + format_source(data["source"])

    @mcp.tool()
    async def kb_add_url(url: str) -> str:
        data = await client.add_url(url)
        return format_message(data["message"]) + "\n\n" + format_source(data["source"])

    @mcp.tool()
    async def kb_add_local(path: str, include: Optional[List[str]] = None, exclude: Optional[List[str]] = None) -> str:
        data = await client.add_local(path, include, exclude)
        return format_message(data["message"]) + "\n\n" + format_source(data["source"])

    @mcp.tool()
    async def kb_add_site(base_url: str, max_pages: Optional[int] = None) -> str:
        data = await client.add_site(base_url, max_pages)
        return format_message(data["message"]) + "\n\n" + format_source(data["source"])

    @mcp.tool()
    async def kb_search(query: str, n_results: int = 5, source_filter: Optional[str] = None) -> str:
        return format_search(await client.search(query, n_results, source_filter))

    @mcp.tool()
    async def kb_list(source_type: Optional[str] = None) -> str:
        return format_sources(await client.list_sources(source_type))

    @mcp.tool()
    async def kb_delete(source_id: str) -> str:
        await client.delete(source_id)
        return format_message(f"Deleted {source_id}")

    @mcp.tool()
    async def kb_status() -> str:
        return format_status(await client.status())

    @mcp.tool()
    async def kb_progress(source_id: str) -> str:
        return format_source((await client.progress(source_id))["source"])

    @mcp.tool()
    async def kb_update(source_id: Optional[str] = None) -> str:
        data = await client.update(source_id)
        return format_message(data["message"])

    @mcp.tool()
    async def kb_reindex(source_id: Optional[str] = None) -> str:
        data = await client.reindex(source_id)
        return format_message(data["message"])

    return mcp


try:
    server = create_server()
except Exception:
    server = None

if __name__ == "__main__":
    if server:
        server.run()
    else:
        print('Failed to create server. Please check configuration.')
