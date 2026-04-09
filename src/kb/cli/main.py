#!/usr/bin/env python3
"""CLI for the knowledge base service."""
import asyncio
import os
import sys
from pathlib import Path

from kb.client.http import KBHttpClient
from kb.config import Config, DEFAULT_CONFIG_PATH, resolve_config_path
from kb.http.process_manager import read_logs, restart, serve, stop
from kb.presenters import format_message, format_search, format_source, format_sources, format_status


class KnowledgeBaseCLI:
    def __init__(self):
        self.config_path = self._writable_config_path()
        self.config = Config.load_from_file(resolve_config_path(os.getenv("KNOWLEDGE_BASE_CONFIG")))
        self.client = KBHttpClient(self.config)

    @staticmethod
    def _writable_config_path() -> Path:
        override = os.getenv("KNOWLEDGE_BASE_CONFIG")
        if override:
            return Path(override).expanduser()
        return DEFAULT_CONFIG_PATH

    def _save_config(self) -> None:
        self.config.save_to_file(self.config_path)
        self.client = KBHttpClient(self.config)

    async def status(self):
        print(format_status(await self.client.status()))

    async def list_sources(self, source_type=None):
        print(format_sources(await self.client.list_sources(source_type)))

    async def add_url(self, url):
        data = await self.client.add_url(url)
        print(format_message(data["message"]))
        print()
        print(format_source(data["source"]))

    async def add_repo(self, repo_url, branch=None):
        data = await self.client.add_repo(repo_url, branch)
        print(format_message(data["message"]))
        print()
        print(format_source(data["source"]))

    async def add_local(self, path):
        data = await self.client.add_local(path)
        print(format_message(data["message"]))
        print()
        print(format_source(data["source"]))

    async def add_site(self, base_url, max_pages=None):
        data = await self.client.add_site(base_url, max_pages)
        print(format_message(data["message"]))
        print()
        print(format_source(data["source"]))

    async def search(self, query, n_results=5):
        print(format_search(await self.client.search(query, n_results=n_results)))

    async def delete(self, source_id):
        await self.client.delete(source_id)
        print(format_message(f"Deleted {source_id}"))

    async def progress(self, source_id):
        print(format_source((await self.client.progress(source_id))["source"]))

    async def reindex(self, source_id=None):
        data = await self.client.reindex(source_id)
        print(format_message(data["message"]))
        if source_id:
            print()
            print(format_source(data["source"]))

    async def update(self, source_id=None):
        data = await self.client.update(source_id)
        print(format_message(data["message"]))
        if source_id:
            print()
            print(format_source(data["source"]))

    def connect(self, target: str | None):
        if not target:
            print(format_message(f"Connected to {self.config.service.effective_base_url}"))
            return
        if target in {"local", "--local"}:
            self.config.service.base_url = None
            self._save_config()
            print(format_message(f"Using local service at {self.config.service.local_url}"))
            return
        self.config.service.base_url = target.rstrip("/")
        self._save_config()
        print(format_message(f"Connected to remote service {self.config.service.base_url}"))


def print_usage():
    print("Knowledge Base CLI")
    print("\nUsage:")
    print("  kb status")
    print("  kb list [github_repo|web_page|web_site|local]")
    print("  kb progress <source-id>")
    print("  kb add-url <url>")
    print("  kb add-site <base-url> [max-pages]")
    print("  kb add-repo <owner/repo> [branch]")
    print("  kb add-local <path>")
    print("  kb search <query>")
    print("  kb delete <source-id>")
    print("  kb update [source-id|--all]")
    print("  kb reindex [source-id|--all]")
    print("  kb serve | stop | restart | logs [lines]")
    print("  kb connect [http://host:port|local]")


async def async_main():
    if len(sys.argv) < 2:
        print_usage()
        return

    cli = KnowledgeBaseCLI()
    command = sys.argv[1]

    if command == "serve":
        print(format_message(serve()))
        return
    if command == "stop":
        print(format_message(stop()))
        return
    if command == "restart":
        print(format_message(restart()))
        return
    if command == "logs":
        lines = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        print(read_logs(lines))
        return
    if command == "connect":
        cli.connect(sys.argv[2] if len(sys.argv) > 2 else None)
        return

    try:
        if command == "status":
            await cli.status()
        elif command == "list":
            await cli.list_sources(sys.argv[2] if len(sys.argv) > 2 else None)
        elif command == "progress":
            await cli.progress(sys.argv[2])
        elif command == "add-url":
            await cli.add_url(sys.argv[2])
        elif command == "add-site":
            max_pages = int(sys.argv[3]) if len(sys.argv) > 3 else None
            await cli.add_site(sys.argv[2], max_pages)
        elif command == "add-repo":
            branch = sys.argv[3] if len(sys.argv) > 3 else None
            await cli.add_repo(sys.argv[2], branch)
        elif command == "add-local":
            await cli.add_local(sys.argv[2])
        elif command == "search":
            await cli.search(" ".join(sys.argv[2:]))
        elif command == "delete":
            await cli.delete(sys.argv[2])
        elif command == "update":
            source_id = None if len(sys.argv) < 3 or sys.argv[2] == "--all" else sys.argv[2]
            await cli.update(source_id)
        elif command == "reindex":
            source_id = None if len(sys.argv) < 3 or sys.argv[2] == "--all" else sys.argv[2]
            await cli.reindex(source_id)
        else:
            print_usage()
    except IndexError:
        print_usage()
    except Exception as exc:
        print(f"Error: {exc}")
        raise


if __name__ == "__main__":
    asyncio.run(async_main())


def cli_entry():
    asyncio.run(async_main())
