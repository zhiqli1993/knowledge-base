---
name: knowledge-base
description: Manage a local or remote knowledge base service for indexing and searching local files, GitHub repositories, web pages, and documentation sites. Use when the user wants to add/search/manage content in their KB.
---

# Knowledge Base Skill

This skill works with the MCP tools provided by `kb.mcp.server`.

## Available operations

- Add repo: `mcp__knowledge-base__kb_add_repo`
- Add URL: `mcp__knowledge-base__kb_add_url`
- Add local path: `mcp__knowledge-base__kb_add_local`
- Add site: `mcp__knowledge-base__kb_add_site`
- Search: `mcp__knowledge-base__kb_search`
- List sources: `mcp__knowledge-base__kb_list`
- Status: `mcp__knowledge-base__kb_status`
- Progress: `mcp__knowledge-base__kb_progress`
- Update: `mcp__knowledge-base__kb_update`
- Reindex: `mcp__knowledge-base__kb_reindex`
- Delete: `mcp__knowledge-base__kb_delete`

## Guidance

- If the user asks to add a local path, remember it is validated against `local.allowed_paths`
- If the user needs to know whether indexing is done, use `kb_progress` or `kb_status`
- If results are stale, prefer `kb_update` or `kb_reindex`
- If the user is operating locally and the KB appears unavailable, suggest `kb serve`
