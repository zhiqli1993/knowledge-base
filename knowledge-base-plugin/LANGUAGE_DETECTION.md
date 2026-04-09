# Language-Specific Exclude Patterns

## Overview

When indexing GitHub repositories, Knowledge Base can auto-detect the dominant language and apply optimized exclude patterns to avoid indexing build artifacts and dependency directories.

This behavior happens in the repository indexing pipeline used by the KB web service.

## Supported Languages

### Go

Common excludes:

- `**/vendor/**`
- `**/bin/**`
- `**/*.test`

### Python

Common excludes:

- `**/__pycache__/**`
- `**/venv/**`
- `**/.venv/**`
- `**/env/**`
- `**/site-packages/**`
- `**/*.pyc`
- `**/*.pyo`
- `**/*.egg-info/**`
- `**/dist/**`
- `**/build/**`

### JavaScript / TypeScript

Common excludes:

- `**/node_modules/**`
- `**/dist/**`
- `**/build/**`
- `**/.next/**`
- `**/.nuxt/**`
- `**/coverage/**`

### Java

Common excludes:

- `**/target/**`
- `**/.gradle/**`
- `**/build/**`
- `**/*.class`
- `**/*.jar`
- `**/*.war`

### Rust

Common excludes:

- `**/target/**`
- `**/*.rlib`
- `**/*.so`

### C / C++

Common excludes:

- `**/build/**`
- `**/cmake-build-*/**`
- `**/*.o`
- `**/*.a`
- `**/*.so`
- `**/*.dylib`

## How It Works

1. The repo is cloned with shallow history.
2. File extensions are sampled across the working tree.
3. A dominant language is inferred.
4. Language-specific excludes are applied on top of common excludes.
5. Remaining files are chunked and indexed.

## Default Usage

You do not need to do anything special.

```bash
kb add-repo fastapi/fastapi
```

If auto-detection is enabled, the service will infer the language and skip common irrelevant files.

## Global Configuration

Edit `~/.kb/config.json`:

```json
{
  "github": {
    "max_file_size_mb": 5,
    "auto_detect_language": true
  }
}
```

Set `auto_detect_language` to `false` if you want to disable language inference.

## Manual Include / Exclude Control

You can still pass explicit patterns when adding a repo.

CLI example:

```bash
kb add-repo owner/repo main
```

MCP example:

- `kb_add_repo(repo_url="owner/repo", include=[...], exclude=[...])`

Use explicit include/exclude patterns when:

- the repository is mixed-language
- dominant-language inference is misleading
- you want to sharply reduce indexing scope

## Common Excludes Applied Everywhere

Regardless of language, the pipeline also avoids common junk such as:

- `.git`
- build output
- dependency directories
- generated artifacts

## Troubleshooting

### Wrong language inferred

Pass explicit `exclude` patterns or narrower `include` patterns.

### Too many files indexed

Use explicit includes like:

- `docs/**`
- `src/**`
- `**/*.md`
- `**/*.py`

### Important files skipped

Override with narrower manual includes instead of relying on auto-detection.

## Related Docs

- `README.md`
- `USAGE.md`
- `knowledge-base-plugin/QUICKSTART.md`
