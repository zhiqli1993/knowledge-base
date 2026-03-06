# Phase 2: GitHub Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Implement GitHub repository integration to fetch files and extract knowledge from repos.

**Architecture:** GitHub adapter using PyGithub for API access, respecting rate limits, with smart file filtering.

**Tech Stack:** PyGithub, asyncio, smart pattern matching for file inclusion/exclusion

---

## Phase 2: GitHub Integration

### Task 1: GitHub File Info Model

**Files:**
- Create: `mcp_server/sources/file_info.py`
- Test: `tests/unit/sources/test_file_info.py`

**Step 1: Write file info model test**

Create: `tests/unit/sources/test_file_info.py`

```python
from mcp_server.sources.file_info import FileInfo

def test_file_info_creation():
    """Test FileInfo model creation"""
    file_info = FileInfo(
        path="src/index.ts",
        url="https://github.com/owner/repo/blob/main/src/index.ts",
        size=1024,
        sha="abc123",
        language="typescript"
    )
    assert file_info.path == "src/index.ts"
    assert file_info.language == "typescript"

def test_file_info_from_github_content():
    """Test creating FileInfo from GitHub ContentFile"""
    # Mock GitHub ContentFile structure
    mock_content = type('obj', (object,), {
        'path': 'README.md',
        'html_url': 'https://github.com/owner/repo/blob/main/README.md',
        'size': 2048,
        'sha': 'def456'
    })()

    file_info = FileInfo.from_github_content(mock_content, 'owner/repo')
    assert file_info.path == 'README.md'
    assert file_info.size == 2048
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/sources/test_file_info.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Implement FileInfo model**

Create: `mcp_server/sources/file_info.py`

```python
from typing import Optional
from pydantic import BaseModel
from pathlib import Path

class FileInfo(BaseModel):
    path: str
    url: str
    size: int
    sha: str
    language: Optional[str] = None

    @classmethod
    def from_github_content(cls, content, repo_name: str) -> "FileInfo":
        """Create FileInfo from GitHub ContentFile"""
        # Detect language from file extension
        ext = Path(content.path).suffix.lstrip('.')
        lang_map = {
            'md': 'markdown',
            'py': 'python',
            'ts': 'typescript',
            'tsx': 'typescript',
            'js': 'javascript',
            'jsx': 'javascript',
            'go': 'go',
            'rs': 'rust',
            'java': 'java',
        }

        return cls(
            path=content.path,
            url=content.html_url,
            size=content.size,
            sha=content.sha,
            language=lang_map.get(ext, 'text')
        )

    async def download(self) -> str:
        """Download file content (to be implemented)"""
        raise NotImplementedError("Subclass must implement download()")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/sources/test_file_info.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add mcp_server/sources/file_info.py tests/unit/sources/test_file_info.py
git commit -m "feat: add FileInfo model for GitHub file metadata"
```

---

### Task 2: GitHub Repository Fetcher

**Files:**
- Create: `mcp_server/sources/github.py`
- Test: `tests/unit/sources/test_github.py`

**Step 1: Write GitHub fetcher test**

Create: `tests/unit/sources/test_github.py`

```python
import pytest
from mcp_server.sources.github import GitHubRepoFetcher
from mcp_server.config import GitHubConfig

def test_parse_repo_url():
    """Test parsing GitHub repo URL"""
    config = GitHubConfig()
    fetcher = GitHubRepoFetcher("https://github.com/owner/repo", config)

    assert fetcher.owner == "owner"
    assert fetcher.repo_name == "repo"

def test_parse_short_repo_url():
    """Test parsing short GitHub repo format"""
    config = GitHubConfig()
    fetcher = GitHubRepoFetcher("owner/repo", config)

    assert fetcher.owner == "owner"
    assert fetcher.repo_name == "repo"

def test_should_include_file():
    """Test file inclusion logic"""
    config = GitHubConfig()
    fetcher = GitHubRepoFetcher("owner/repo", config)

    # Default includes
    assert fetcher.should_include("README.md") is True
    assert fetcher.should_include("docs/guide.md") is True
    assert fetcher.should_include("src/index.ts") is True

    # Default excludes
    assert fetcher.should_include("node_modules/package.json") is False
    assert fetcher.should_include("dist/bundle.js") is False
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/sources/test_github.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Implement GitHub fetcher**

Create: `mcp_server/sources/github.py`

```python
import re
from typing import List, Optional, Dict, Any
from pathlib import Path
from github import Github
from mcp_server.config import GitHubConfig
from mcp_server.sources.file_info import FileInfo

class GitHubRepoFetcher:
    def __init__(
        self,
        repo_url: str,
        config: GitHubConfig,
        branch: str = "main",
        include: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None
    ):
        self.config = config
        self.branch = branch
        self.include_patterns = include or [
            "**/*.md", "**/README*", "**/docs/**",
            "**/*.ts", "**/*.py", "**/*.go"
        ]
        self.exclude_patterns = exclude or [
            "**/node_modules/**", "**/.git/**", "**/dist/**",
            "**/build/**", "**/*.test.*", "**/*.spec.*"
        ]

        # Parse repo URL
        self.owner, self.repo_name = self._parse_repo_url(repo_url)

        # Initialize GitHub client
        if config.token:
            self.github = Github(config.token)
        else:
            self.github = Github()

        self.repo = self.github.get_repo(f"{self.owner}/{self.repo_name}")

    def _parse_repo_url(self, repo_url: str) -> tuple[str, str]:
        """Parse GitHub repo URL to extract owner and repo name"""
        # Handle full URL: https://github.com/owner/repo
        if repo_url.startswith("http"):
            match = re.match(r'https?://github\.com/([^/]+)/([^/]+)', repo_url)
            if match:
                return match.group(1), match.group(2)

        # Handle short format: owner/repo
        if '/' in repo_url:
            parts = repo_url.split('/')
            return parts[0], parts[1]

        raise ValueError(f"Invalid GitHub repo URL: {repo_url}")

    def should_include(self, file_path: str) -> bool:
        """Check if file should be included based on patterns"""
        path = Path(file_path)

        # Check exclude patterns first
        for pattern in self.exclude_patterns:
            if path.match(pattern):
                return False

        # Check include patterns
        for pattern in self.include_patterns:
            if path.match(pattern):
                return True

        return False

    async def list_files(self) -> List[FileInfo]:
        """List all files in repository matching patterns"""
        files = []

        try:
            contents = self.repo.get_contents("", ref=self.branch)

            while contents:
                file_content = contents.pop(0)

                if file_content.type == "dir":
                    # Recursively get directory contents
                    contents.extend(self.repo.get_contents(file_content.path, ref=self.branch))
                else:
                    # Check if file should be included
                    if self.should_include(file_content.path):
                        # Check file size limit
                        if file_content.size <= self.config.max_file_size_mb * 1024 * 1024:
                            file_info = FileInfo.from_github_content(
                                file_content,
                                f"{self.owner}/{self.repo_name}"
                            )
                            # Add download method
                            file_info.download = lambda fc=file_content: self._download_content(fc)
                            files.append(file_info)

        except Exception as e:
            raise RuntimeError(f"Failed to list files from {self.owner}/{self.repo_name}: {e}")

        return files

    async def _download_content(self, file_content) -> str:
        """Download file content from GitHub"""
        try:
            content = file_content.decoded_content.decode('utf-8')
            return content
        except Exception as e:
            raise RuntimeError(f"Failed to download {file_content.path}: {e}")

    def close(self):
        """Close GitHub client connection"""
        if hasattr(self.github, 'close'):
            self.github.close()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/sources/test_github.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add mcp_server/sources/github.py tests/unit/sources/test_github.py
git commit -m "feat: add GitHub repository fetcher with pattern matching"
```

---

### Task 3: Integration Test with Mock GitHub API

**Files:**
- Test: `tests/integration/test_github_integration.py`

**Step 1: Write integration test**

Create: `tests/integration/test_github_integration.py`

```python
import pytest
from unittest.mock import Mock, patch
from mcp_server.sources.github import GitHubRepoFetcher
from mcp_server.config import GitHubConfig

@pytest.mark.asyncio
async def test_github_fetcher_integration():
    """Test GitHub fetcher with mocked API"""

    # Mock GitHub API responses
    mock_repo = Mock()
    mock_repo.get_contents.return_value = [
        Mock(
            type='file',
            path='README.md',
            html_url='https://github.com/owner/repo/blob/main/README.md',
            size=1024,
            sha='abc123',
            decoded_content=b'# Test README'
        ),
        Mock(
            type='file',
            path='node_modules/package.json',
            html_url='https://github.com/owner/repo/blob/main/node_modules/package.json',
            size=512,
            sha='def456',
            decoded_content=b'{}'
        )
    ]

    with patch('mcp_server.sources.github.Github') as mock_github:
        mock_github.return_value.get_repo.return_value = mock_repo

        config = GitHubConfig()
        fetcher = GitHubRepoFetcher("owner/repo", config)
        files = await fetcher.list_files()

        # Should include README.md but exclude node_modules
        assert len(files) == 1
        assert files[0].path == 'README.md'
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_github_integration.py -v`
Expected: FAIL (implementation issues to fix)

**Step 3: Fix any issues**

(Adjust implementation based on test failures)

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_github_integration.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/integration/test_github_integration.py
git commit -m "test: add GitHub integration test with mocked API"
```

---

## Summary

Phase 2 adds GitHub integration with:
- FileInfo model for file metadata
- GitHubRepoFetcher for repository traversal
- Pattern-based file filtering (include/exclude)
- File size limits
- Integration tests with mocked GitHub API

**Next Phase (Phase 3):** Web scraping integration with trafilatura

---

## Execution Options

**1. Subagent-Driven (this session)** - Continue with fresh subagents per task
**2. Parallel Session (separate)** - Open new session with executing-plans

Which approach?
