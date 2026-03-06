import re
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class ChunkResult:
    text: str
    metadata: Dict[str, Any]

class Chunker:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, content: str, file_path: str) -> List[ChunkResult]:
        """Chunk content based on file type"""
        language = self.detect_language(file_path)

        if language == "markdown":
            return self.chunk_markdown(content)
        else:
            return self.chunk_plain_text(content)

    def detect_language(self, file_path: str) -> str:
        """Detect language from file extension"""
        ext = file_path.split(".")[-1].lower()

        lang_map = {
            "md": "markdown",
            "py": "python",
            "ts": "typescript",
            "tsx": "typescript",
            "js": "javascript",
            "jsx": "javascript",
            "go": "go",
            "rs": "rust",
            "java": "java",
        }

        return lang_map.get(ext, "text")

    def chunk_markdown(self, content: str) -> List[ChunkResult]:
        """Chunk markdown by header hierarchy"""
        chunks = []

        # Split by headers
        lines = content.split("\n")
        current_chunk = []
        current_headers = []
        current_size = 0

        for line in lines:
            # Check if line is a header
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)

            if header_match:
                # Save current chunk if it exists
                if current_chunk:
                    chunks.append(ChunkResult(
                        text="\n".join(current_chunk),
                        metadata={"headers": current_headers.copy()}
                    ))
                    current_chunk = []
                    current_size = 0

                # Update header breadcrumb
                level = len(header_match.group(1))
                header_text = header_match.group(2)

                # Remove headers of same or lower level
                current_headers = [h for h in current_headers if h[0] < level]
                current_headers.append((level, header_text))

            current_chunk.append(line)
            current_size += len(line)

            # Split if chunk is too large
            if current_size > self.chunk_size and not header_match:
                chunks.append(ChunkResult(
                    text="\n".join(current_chunk),
                    metadata={"headers": current_headers.copy()}
                ))
                current_chunk = []
                current_size = 0

        # Add final chunk
        if current_chunk:
            chunks.append(ChunkResult(
                text="\n".join(current_chunk),
                metadata={"headers": current_headers.copy()}
            ))

        return chunks

    def chunk_plain_text(self, content: str) -> List[ChunkResult]:
        """Chunk plain text with sliding window"""
        chunks = []
        start = 0

        while start < len(content):
            end = start + self.chunk_size
            chunk_text = content[start:end]

            chunks.append(ChunkResult(
                text=chunk_text,
                metadata={}
            ))

            start += (self.chunk_size - self.chunk_overlap)

        return chunks