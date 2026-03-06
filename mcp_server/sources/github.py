import re
import fnmatch
from typing import List, Optional
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

        # Initialize GitHub client (lazy)
        self._github: Optional[Github] = None
        self._repo = None

    @property
    def github(self) -> Github:
        """Lazy initialize GitHub client"""
        if self._github is None:
            if self.config.token:
                self._github = Github(self.config.token)
            else:
                self._github = Github()
        return self._github

    @property
    def repo(self):
        """Lazy initialize repo"""
        if self._repo is None:
            self._repo = self.github.get_repo(f"{self.owner}/{self.repo_name}")
        return self._repo

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

        # Also check if filename matches include patterns directly
        filename = path.name
        for pattern in self.include_patterns:
            if fnmatch.fnmatch(filename, pattern.replace("**/", "")):
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
                                f"{self.owner}/{self.repo_name}",
                                file_content.decoded_content.decode('utf-8')
                            )
                            files.append(file_info)

        except Exception as e:
            raise RuntimeError(f"Failed to list files from {self.owner}/{self.repo_name}: {e}")

        return files

    def close(self):
        """Close GitHub client connection"""
        if self._github and hasattr(self._github, 'close'):
            self._github.close()