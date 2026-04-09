"""Local filesystem source adapter."""
import asyncio
from pathlib import Path
from typing import List, Optional
import fnmatch

from kb.core.local_access import is_path_allowed
from kb.sources.file_info import FileInfo


class LocalFileCollector:
    """Collect readable local files from a file or directory path."""

    def __init__(
        self,
        source_path: str,
        include: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None,
        max_file_size_mb: int = 5,
        allowed_roots: Optional[List[Path]] = None,
        allow_unrestricted: bool = False,
    ):
        self.source_path = Path(source_path).expanduser().resolve()
        self.include_patterns = include or []
        self.exclude_patterns = exclude or []
        self.max_size_bytes = max_file_size_mb * 1024 * 1024
        self.allowed_roots = [root.expanduser().resolve() for root in (allowed_roots or [])]
        self.allow_unrestricted = allow_unrestricted

        if not self.source_path.exists():
            raise FileNotFoundError(f"Local path does not exist: {self.source_path}")

    def should_include(self, relative_path: Path) -> bool:
        """Check whether a relative path should be indexed."""
        path_str = relative_path.as_posix()

        for pattern in self.exclude_patterns:
            if self._matches_pattern(relative_path, path_str, pattern):
                return False

        if not self.include_patterns:
            return True

        for pattern in self.include_patterns:
            if self._matches_pattern(relative_path, path_str, pattern):
                return True

        return False

    @staticmethod
    def _matches_pattern(relative_path: Path, path_str: str, pattern: str) -> bool:
        """Match patterns while treating leading '**/' as optional for root files."""
        if relative_path.match(pattern) or fnmatch.fnmatch(path_str, pattern):
            return True

        if pattern.startswith("**/"):
            normalized_pattern = pattern[3:]
            return (
                relative_path.match(normalized_pattern)
                or fnmatch.fnmatch(path_str, normalized_pattern)
            )

        return False

    def _iter_files(self) -> List[Path]:
        """Return candidate files for indexing."""
        if self.source_path.is_file():
            return [self.source_path] if self._is_allowed_path(self.source_path) else []

        files: List[Path] = []
        for file_path in self.source_path.rglob("*"):
            if file_path.is_dir():
                continue

            relative_path = file_path.relative_to(self.source_path)
            if self.should_include(relative_path) and self._is_allowed_path(file_path):
                files.append(file_path)

        return files

    async def list_files(self) -> List[FileInfo]:
        """List readable files from the local source."""
        files: List[FileInfo] = []
        is_single_file = self.source_path.is_file()
        candidate_files = await asyncio.to_thread(self._iter_files)

        for file_path in candidate_files:
            file_info = await asyncio.to_thread(
                self._build_file_info,
                file_path,
                is_single_file,
            )
            if file_info is not None:
                files.append(file_info)

        return files

    def _build_file_info(self, file_path: Path, is_single_file: bool) -> Optional[FileInfo]:
        """Build FileInfo for a readable local file."""
        if not self._is_allowed_path(file_path):
            return None

        try:
            file_size = file_path.stat().st_size
            if file_size > self.max_size_bytes:
                return None

            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except (OSError, PermissionError, UnicodeDecodeError):
            return None

        relative_path = (
            file_path.name
            if is_single_file
            else file_path.relative_to(self.source_path).as_posix()
        )

        return FileInfo(
            path=relative_path,
            url=file_path.as_uri(),
            size=file_size,
            content=content,
        )

    def _is_allowed_path(self, file_path: Path) -> bool:
        """Check whether a file stays within approved local roots."""
        if not self.allowed_roots and not self.allow_unrestricted:
            return True

        return is_path_allowed(
            file_path.resolve(),
            self.allowed_roots,
            self.allow_unrestricted,
        )
