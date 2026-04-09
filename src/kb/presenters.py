from typing import Any, Dict, List


def _box(title: str, lines: List[str]) -> str:
    width = max([len(title)] + [len(line) for line in lines] + [20])
    top = f"┌─ {title} {'─' * max(0, width - len(title) - 1)}┐"
    body = [f"│ {line.ljust(width)} │" for line in lines]
    bottom = f"└{'─' * (width + 2)}┘"
    return "\n".join([top, *body, bottom])


def format_status(data: Dict[str, Any]) -> str:
    src = data["sources"]
    return _box(
        "KB Status",
        [
            f"Sources  total={src['total']} ready={src['indexed']} indexing={src['indexing']} pending={src['pending']} failed={src['failed']}",
            f"Docs     {data['documents']}",
            f"Chunks   {data['chunks']}",
            f"Storage  {data['storage']}",
            f"Embed    {data['embedding_model']}",
            f"Service  {data['service']['base_url']}",
        ],
    )


def format_source(source: Dict[str, Any]) -> str:
    progress_total = source.get("progress_total") or 0
    progress_processed = source.get("progress_processed") or 0
    progress_pct = int((progress_processed / progress_total) * 100) if progress_total else 0
    lines = [
        f"ID       {source['id']}",
        f"Type     {source['type']}",
        f"URL      {source['url']}",
        f"Status   {source['status']}",
        f"Docs     {source.get('document_count', 0)}",
        f"Chunks   {source.get('chunk_count', 0)}",
    ]
    if source.get("last_indexed_at"):
        lines.append(f"Indexed  {source['last_indexed_at']}")
    if source.get("progress_phase"):
        lines.append(
            f"Progress {progress_processed}/{progress_total} ({progress_pct}%) {source.get('progress_phase')}"
        )
    if source.get("progress_message"):
        lines.append(f"Message  {source['progress_message']}")
    if source.get("error_message"):
        lines.append(f"Error    {source['error_message']}")
    return _box(source.get("name") or source["id"], lines)


def format_sources(data: Dict[str, Any]) -> str:
    sources = data.get("sources", [])
    if not sources:
        return format_message("No sources found.")
    return "\n\n".join(format_source(source) for source in sources)


def format_search(data: Dict[str, Any]) -> str:
    results = data.get("results", [])
    if not results:
        return format_message("No results found.")
    blocks = []
    for index, result in enumerate(results, start=1):
        lines = [
            f"Score   {result['score']:.3f}",
            f"Source  {result['source_id']}",
            f"File    {result['file_path']}",
            "",
            result["text"],
        ]
        blocks.append(_box(f"Result {index}", lines))
    return "\n\n".join(blocks)


def format_message(message: str) -> str:
    return _box("KB", [message])


def format_error(message: str) -> str:
    return _box("KB Error", [message])


def format_logs(content: str) -> str:
    lines = content.splitlines() or [content]
    return _box("KB Logs", lines)


def format_usage() -> str:
    return _box(
        "Knowledge Base CLI",
        [
            "Usage:",
            "  kb status",
            "  kb list [github_repo|web_page|web_site|local]",
            "  kb progress <source-id>",
            "  kb add-url <url>",
            "  kb add-site <base-url> [max-pages]",
            "  kb add-repo <owner/repo|https-url> [branch]",
            "  kb add-local <path>",
            "  kb search <query>",
            "  kb delete <source-id>",
            "  kb update [source-id|--all]",
            "  kb reindex [source-id|--all]",
            "  kb serve | stop | restart | logs [lines]",
            "  kb connect [http://host:port|local]",
        ],
    )
