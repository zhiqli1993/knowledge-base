"""GitHub repository fetcher using git clone (no API token needed)"""
import tempfile
import shutil
from pathlib import Path
from typing import List, Optional
import subprocess
import fnmatch
from kb.sources.file_info import FileInfo


class GitHubRepoCloner:
    """Fetch GitHub repository by cloning it locally"""

    # Language-specific exclude patterns
    LANGUAGE_EXCLUDES = {
        "go": [
            "**/vendor/**",      # Go dependencies
            "**/bin/**",         # Compiled binaries
            "**/*.test",         # Test binaries
        ],
        "python": [
            "**/__pycache__/**", # Python bytecode
            "**/venv/**",        # Virtual environment
            "**/env/**",         # Alternative venv name
            "**/.venv/**",       # Hidden venv
            "**/site-packages/**", # Installed packages
            "**/*.pyc",          # Compiled Python files
            "**/*.pyo",          # Optimized bytecode
            "**/*.egg-info/**",  # Package metadata
            "**/dist/**",        # Distribution files
            "**/build/**",       # Build artifacts
        ],
        "javascript": [
            "**/node_modules/**", # npm/yarn dependencies
            "**/dist/**",        # Build output
            "**/build/**",       # Build directory
            "**/.next/**",       # Next.js build
            "**/.nuxt/**",       # Nuxt.js build
            "**/coverage/**",    # Test coverage
        ],
        "typescript": [
            "**/node_modules/**", # npm/yarn dependencies
            "**/dist/**",        # Build output
            "**/build/**",       # Build directory
            "**/.next/**",       # Next.js build
            "**/coverage/**",    # Test coverage
        ],
        "java": [
            "**/target/**",      # Maven build
            "**/.gradle/**",     # Gradle cache
            "**/build/**",       # Gradle build
            "**/*.class",        # Compiled classes
            "**/*.jar",          # JAR files
            "**/*.war",          # WAR files
        ],
        "rust": [
            "**/target/**",      # Cargo build
            "**/*.rlib",         # Rust libraries
            "**/*.so",           # Shared objects
        ],
        "cpp": [
            "**/build/**",       # CMake build
            "**/cmake-build-*/**", # CLion builds
            "**/*.o",            # Object files
            "**/*.a",            # Static libraries
            "**/*.so",           # Shared libraries
            "**/*.dylib",        # macOS libraries
        ],
    }

    # Common excludes for all projects
    COMMON_EXCLUDES = [
        "**/.git/**",        # Git metadata
        "**/*.test.*",       # Test files
        "**/*.spec.*",       # Spec files
        "**/.*",             # Hidden files (except .md)
    ]

    def __init__(
        self,
        repo_url: str,
        branch: str = "main",
        include: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None,
        max_file_size_mb: int = 5,
        auto_detect_language: bool = True
    ):
        self.repo_url = self._normalize_url(repo_url)
        self.branch = branch
        self.max_file_size_mb = max_file_size_mb
        self.auto_detect = auto_detect_language

        self.include_patterns = include or [
            "**/*.md", "**/README*", "**/docs/**",
            "**/*.ts", "**/*.py", "**/*.go", "**/*.js",
            "**/*.java", "**/*.rs", "**/*.cpp", "**/*.c"
        ]

        # Use provided exclude patterns or auto-detect
        self.exclude_patterns = exclude
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
        path_str = file_path.as_posix()
        exclude_patterns = self.exclude_patterns if self.exclude_patterns is not None else self._get_exclude_patterns()

        # Check exclude patterns first
        for pattern in exclude_patterns:
            if self._matches_pattern(file_path, path_str, pattern):
                return False

        # Check include patterns
        for pattern in self.include_patterns:
            if self._matches_pattern(file_path, path_str, pattern):
                return True

        return False

    @staticmethod
    def _matches_pattern(file_path: Path, path_str: str, pattern: str) -> bool:
        """Match patterns while treating leading '**/' as optional for root files."""
        if file_path.match(pattern) or fnmatch.fnmatch(path_str, pattern):
            return True

        if pattern.startswith("**/"):
            normalized_pattern = pattern[3:]
            return (
                file_path.match(normalized_pattern)
                or fnmatch.fnmatch(path_str, normalized_pattern)
            )

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

    def _detect_language(self) -> Optional[str]:
        """Detect primary language of repository by file extensions"""
        if not self.repo_path:
            return None

        # Count files by extension
        extension_counts = {}
        for file_path in self.repo_path.rglob("*"):
            if file_path.is_file() and ".git" not in file_path.parts:
                ext = file_path.suffix.lower()
                if ext:
                    extension_counts[ext] = extension_counts.get(ext, 0) + 1

        if not extension_counts:
            return None

        # Map extensions to languages
        ext_to_lang = {
            ".go": "go",
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".java": "java",
            ".rs": "rust",
            ".cpp": "cpp",
            ".cc": "cpp",
            ".c": "cpp",
            ".h": "cpp",
        }

        # Find most common language
        lang_counts = {}
        for ext, count in extension_counts.items():
            if ext in ext_to_lang:
                lang = ext_to_lang[ext]
                lang_counts[lang] = lang_counts.get(lang, 0) + count

        if lang_counts:
            return max(lang_counts, key=lang_counts.get)
        return None

    def _get_exclude_patterns(self) -> List[str]:
        """Get exclude patterns based on detected or specified language"""
        if self.exclude_patterns is not None:
            # User provided explicit exclude patterns
            return self.exclude_patterns

        # Start with common excludes
        patterns = self.COMMON_EXCLUDES.copy()

        # Auto-detect language and add language-specific excludes
        if self.auto_detect:
            detected_lang = self._detect_language()
            if detected_lang and detected_lang in self.LANGUAGE_EXCLUDES:
                patterns.extend(self.LANGUAGE_EXCLUDES[detected_lang])
            else:
                # Fallback: include all common language excludes
                for lang_patterns in self.LANGUAGE_EXCLUDES.values():
                    patterns.extend(lang_patterns)
        else:
            # Include all language excludes if not auto-detecting
            for lang_patterns in self.LANGUAGE_EXCLUDES.values():
                patterns.extend(lang_patterns)

        return list(set(patterns))  # Remove duplicates

    async def list_files(self) -> List[FileInfo]:
        """List all files in repository matching patterns"""
        if not self.repo_path:
            await self.clone_repo()

        # Get exclude patterns (auto-detect language if needed)
        self.exclude_patterns = self._get_exclude_patterns()

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
