from urllib.parse import urlparse
from typing import Optional
import httpx
import trafilatura
from mcp_server.config import WebConfig
from mcp_server.sources.file_info import FileInfo


class WebPageFetcher:
    """Fetch and extract content from web pages"""

    def __init__(self, url: str, config: WebConfig):
        self.url = url
        self.config = config

        # Parse URL
        parsed = urlparse(url)
        self.domain = parsed.netloc
        self.scheme = parsed.scheme

        if not self.scheme:
            self.url = f"https://{url}"
            self.scheme = "https"

    async def fetch_content(self) -> str:
        """Fetch and extract content from web page"""
        async with httpx.AsyncClient(
            timeout=self.config.timeout,
            headers={'User-Agent': self.config.user_agent}
        ) as client:
            try:
                response = await client.get(self.url)
                response.raise_for_status()

                # Extract main content using trafilatura
                content = trafilatura.extract(
                    response.text,
                    include_comments=False,
                    include_tables=True,
                    no_fallback=False
                )

                if not content:
                    raise ValueError(f"Failed to extract content from {self.url}")

                return content

            except httpx.HTTPError as e:
                raise RuntimeError(f"Failed to fetch {self.url}: {e}")

    def get_file_info(self) -> FileInfo:
        """Get FileInfo representation of this page"""
        return FileInfo(
            path=self.url,
            url=self.url,
            size=0,  # Unknown until fetched
            sha="",  # Not applicable for web pages
            language="html"
        )