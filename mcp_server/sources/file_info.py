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