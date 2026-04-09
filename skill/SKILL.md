# Skill: knowledge-base

This skill provides access to the Knowledge Base System, which now uses a **shared KB Web Service backend** plus an MCP proxy layer.

## What it can do

- Add local files or directories
- Add GitHub repositories
- Add single URLs
- Add sitemap-backed sites
- Search indexed content semantically
- Show status and indexing progress
- Reindex or update sources
- Delete sources

## MCP Tools

- `/kb-add-repo <repo-url>`
- `/kb-add-url <url>`
- `/kb-add-local <path>`
- `/kb-add-site <site-url>`
- `/kb-search <query>`
- `/kb-list [source-type]`
- `/kb-status`
- `/kb-progress <source-id>`
- `/kb-update [source-id]`
- `/kb-reindex [source-id]`
- `/kb-delete <source-id>`

## Important Notes

- The MCP server is `kb.mcp.server`
- It proxies the KB Web Service instead of indexing directly
- For local usage, start the service with `kb serve`
- Local file indexing is constrained by `local.allowed_paths` in `~/.kb/config.json`
- When targeting a remote KB service, `add-local` uses the remote machine path

## Recommended Workflow

1. Start the service: `kb serve`
2. Add content with the relevant tool
3. Check `kb-status` or `kb-progress`
4. Search with `kb-search`
