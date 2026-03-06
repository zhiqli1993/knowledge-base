"""GitHub repository fetcher using git clone (no API token needed)"""
import tempfile
import shutil
from pathlib import Path
from typing import List, Optional
import subprocess
import fnmatch
from mcp_server.sources.file_info import FileInfo


class GitHubRepoCloner:
    """Fetch GitHub repository by cloning it locally"""

    def __init__(
        self,
        repo_url: str,
        branch: str = "main",
        include: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None,
        max_file_size_mb: int = 5
    ):
        self.repo_url = self._normalize_url(repo_url)
        self.branch = branch
        self.max_file_size_mb = max_file_size_mb

        self.include_patterns = include or [
            "**/*.md", "**/README*", "**/docs/**",
            "**/*.ts", "**/*.py", "**/*.go", "**/*.js",
            "**/*.java", "**/*.rs", "**/*.cpp", "**/*.c"
        ]
        self.exclude_patterns = exclude or [
            "**/node_modules/**", "**/.git/**", "**/dist/**",
            "**/build/**", "**/*.test.*", "**/*.spec.*",
            "**/vendor/**", "**/target/**", "**/__pycache__/**"
        ]

        self.temp_dir = None
        self.repo_path = None

    def _normalize_url(self, repo_url: str) -> str:
        """Normalize repo URL to https format"""
        # If already full URL, return as is
        if repo_url.startswith("http"):
            return repo_url

        # Convert owner/repo to https URL
        if "/" in repo_url:
            return f"https://github.com/{repo_url}.git"

        raise ValueError(f"Invalid repo URL format: {repo_url}")

    def should_include(self, file_path: Path) -> bool:
        """Check if file should be included based on patterns"""
        path_str = str(file_path)

        # Check exclude patterns first
        for pattern in self.exclude_patterns:
            if file_path.match(pattern) or fnmatch.fnmatch(path_str, pattern):
                return False

        # Check include patterns
        for pattern in self.include_patterns:
            if file_path.match(pattern) or fnmatch.fnmatch(path_str, pattern):
                return True

        return False

    async def clone_repo(self) -> Path:
        """Clone repository to temporary directory"""
        self.temp_dir = tempfile.mkdtemp(prefix="kb_repo_")
        self.repo_path = Path(self.temp_dir) / "repo"

        try:
            # Use shallow clone to save time and space
            cmd = [
                "git", "clone",
                "--depth", "1",  # Shallow clone (only latest commit)
                "--single-branch",  # Only clone the specified branch
                "--branch", self.branch,
                self.repo_url,
                str(self.repo_path)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode != 0:
                raise RuntimeError(
                    f"Git clone failed: {result.stderr}\n"
                    f"Command: {' '.join(cmd)}"
                )

            return self.repo_path

        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Git clone timed out after 5 minutes")
        except Exception as e:
            # Cleanup on error
            if self.temp_dir:
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            raise RuntimeError(f"Failed to clone repository: {e}")

    async def list_files(self) -> List[FileInfo]:
        """List all files in repository matching patterns"""
        if not self.repo_path:
            await self.clone_repo()

        files = []
        max_size_bytes = self.max_file_size_mb * 1024 * 1024

        # Walk through repository
        for file_path in self.repo_path.rglob("*"):
            # Skip directories and .git
            if file_path.is_dir() or ".git" in file_path.parts:
                continue

            # Get relative path from repo root
            rel_path = file_path.relative_to(self.repo_path)

            # Check if file should be included
            if not self.should_include(rel_path):
                continue

            # Check file size
            try:
                file_size = file_path.stat().st_size
                if file_size > max_size_bytes:
                    continue

                # Read file content
                content = file_path.read_text(encoding='utf-8', errors='ignore')

                # Create FileInfo
                file_info = FileInfo(
                    path=str(rel_path),
                    content=content,
                    size=file_size,
                    url=f"{self.repo_url.rstrip('.git')}/blob/{self.branch}/{rel_path}"
                )
                files.append(file_info)

            except (UnicodeDecodeError, PermissionError):
                # Skip binary files or files we can't read
                continue

        return files

    def cleanup(self):
        """Remove temporary clone directory"""
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def __del__(self):
        """Cleanup on deletion"""
        self.cleanup()
