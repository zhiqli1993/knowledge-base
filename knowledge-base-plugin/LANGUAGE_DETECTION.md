# Language-Specific Exclude Patterns

## Overview

Knowledge Base automatically detects the primary language of a GitHub repository and applies optimized exclude patterns to skip common build artifacts and dependencies.

## Supported Languages

### Go
Excludes:
- `**/vendor/**` - Go dependencies
- `**/bin/**` - Compiled binaries
- `**/*.test` - Test binaries

### Python
Excludes:
- `**/__pycache__/**` - Python bytecode
- `**/venv/**`, `**/env/**`, `**/.venv/**` - Virtual environments
- `**/site-packages/**` - Installed packages
- `**/*.pyc`, `**/*.pyo` - Compiled files
- `**/*.egg-info/**` - Package metadata
- `**/dist/**`, `**/build/**` - Build artifacts

### JavaScript/TypeScript
Excludes:
- `**/node_modules/**` - npm/yarn dependencies
- `**/dist/**`, `**/build/**` - Build output
- `**/.next/**` - Next.js build
- `**/.nuxt/**` - Nuxt.js build
- `**/coverage/**` - Test coverage

### Java
Excludes:
- `**/target/**` - Maven build
- `**/.gradle/**`, `**/build/**` - Gradle
- `**/*.class`, `**/*.jar`, `**/*.war` - Compiled artifacts

### Rust
Excludes:
- `**/target/**` - Cargo build
- `**/*.rlib`, `**/*.so` - Compiled libraries

### C/C++
Excludes:
- `**/build/**`, `**/cmake-build-*/**` - Build directories
- `**/*.o`, `**/*.a`, `**/*.so`, `**/*.dylib` - Compiled objects and libraries

## Usage

### Automatic Detection (Default)

```python
# Add repo without specifying exclude patterns
await kb_add_repo("fastapi/fastapi")

# Language is auto-detected from file extensions
# Appropriate exclude patterns are applied automatically
```

### Manual Override

```python
# Provide custom exclude patterns
await kb_add_repo(
    "owner/repo",
    config={
        "exclude": [
            "**/custom_dir/**",
            "**/*.tmp"
        ]
    }
)
```

### Disable Auto-Detection

In `~/.config/knowledge-base/config.json`:

```json
{
  "github": {
    "auto_detect_language": false
  }
}
```

When disabled, all language-specific excludes are applied (superset approach).

## How Detection Works

1. **Clone repository** with `git clone --depth 1`
2. **Count file extensions** in the repository
3. **Map extensions to languages**:
   - `.go` → Go
   - `.py` → Python
   - `.js`, `.jsx` → JavaScript
   - `.ts`, `.tsx` → TypeScript
   - `.java` → Java
   - `.rs` → Rust
   - `.cpp`, `.cc`, `.c`, `.h` → C++
4. **Select most common language** by file count
5. **Apply language-specific excludes** plus common excludes

## Common Excludes (All Projects)

These are always excluded regardless of language:

- `**/.git/**` - Git metadata
- `**/*.test.*` - Test files
- `**/*.spec.*` - Spec files
- `**/.*` - Hidden files (except .md)

## Examples

### Go Project (fastapi/fastapi detected as Python)
```bash
kb_cli.py add-repo fastapi/fastapi

# Auto-detects Python, excludes:
# - __pycache__/
# - venv/
# - *.pyc
# + common excludes
```

### Mixed Language Project
```bash
# Repository with both JS and Python
# Detected language: JavaScript (more .js files)
# Excludes node_modules/ but not venv/

# Solution: Manually specify exclude patterns
kb_cli.py add-repo owner/mixed-repo \
  --exclude "node_modules/**" "venv/**"
```

## Performance Impact

Auto-detection adds minimal overhead:
- **Detection time**: ~10-50ms (single pass through file tree)
- **Clone time**: 1-10 seconds (unchanged)
- **Indexing time**: Significantly reduced by excluding irrelevant files

Example: Node.js project with 50K files in `node_modules/`
- Without exclude: 60 seconds, 50K+ files processed
- With auto-exclude: 5 seconds, ~200 files processed

## Configuration

### Enable/Disable Auto-Detection

Edit `~/.config/knowledge-base/config.json`:

```json
{
  "github": {
    "max_file_size_mb": 5,
    "auto_detect_language": true  // Set to false to disable
  }
}
```

### Custom Language Patterns

Currently not configurable. File an issue if you need custom language support.

## Troubleshooting

### Wrong Language Detected

**Problem**: Repository detected as wrong language

**Solution**: Manually specify exclude patterns:
```python
kb_add_repo(
    "owner/repo",
    config={
        "exclude": ["**/vendor/**", "**/node_modules/**"]
    }
)
```

### Too Many Files Excluded

**Problem**: Important files being excluded

**Solution**: Use explicit include patterns:
```python
kb_add_repo(
    "owner/repo",
    config={
        "include": ["**/*.md", "**/*.py", "**/specific_dir/**"],
        "exclude": []  # Empty exclude = only common excludes
    }
)
```

### New Language Not Supported

**Problem**: Your language (e.g., Scala, Kotlin) not auto-detected

**Workaround**: Manually specify patterns or disable auto-detection

**Long-term**: Submit a PR to add language support

## API Reference

### kb_add_repo Parameters

```python
kb_add_repo(
    repo_url: str,              # "owner/repo" or full URL
    branch: str = "main",       # Git branch
    config: dict = {
        "include": List[str],   # File patterns to include
        "exclude": List[str],   # File patterns to exclude
        "auto_detect_language": bool  # Override global setting
    }
)
```

### GitHubRepoCloner Parameters

```python
GitHubRepoCloner(
    repo_url: str,
    branch: str = "main",
    include: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None,
    max_file_size_mb: int = 5,
    auto_detect_language: bool = True
)
```

## See Also

- [README.md](README.md) - Full documentation
- [USAGE.md](USAGE.md) - Usage examples
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
