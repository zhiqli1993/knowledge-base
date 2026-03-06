from typing import Optional
from pydantic import BaseModel
from pathlib import Path

class FileInfo(BaseModel):
    path: str
    url: str
    size: int
    sha: Optional[str] = None  # Optional for git clone approach
    language: Optional[str] = None
    content: Optional[str] = None

    @classmethod
    def from_github_content(cls, content, repo_name: str, file_content: Optional[str] = None) -> "FileInfo":
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
            language=lang_map.get(ext, 'text'),
            content=file_content
        )

    async def download(self) -> str:
        """Download file content"""
        if self.content is not None:
            return self.content
        raise NotImplementedError("Content not available")