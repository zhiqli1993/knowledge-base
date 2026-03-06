from urllib.parse import urlparse
from typing import Optional, List
import httpx
import trafilatura
from xml.etree import ElementTree as ET
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


class WebSiteFetcher:
    """Fetch URLs from website sitemaps for crawling documentation sites"""

    def __init__(self, base_url: str, config: WebConfig):
        self.base_url = base_url.rstrip('/')
        self.config = config

        parsed = urlparse(base_url)
        self.domain = parsed.netloc
        self.scheme = parsed.scheme or "https"

    async def get_sitemap_urls(self) -> List[str]:
        """Fetch URLs from sitemap.xml or sitemap_index.xml"""
        sitemap_urls = [
            f"{self.base_url}/sitemap_index.xml",
            f"{self.base_url}/sitemap.xml",
        ]

        urls = []

        async with httpx.AsyncClient(
            timeout=self.config.timeout,
            headers={'User-Agent': self.config.user_agent}
        ) as client:
            for sitemap_url in sitemap_urls:
                try:
                    response = await client.get(sitemap_url)
                    if response.status_code == 200:
                        urls = self._parse_sitemap(response.text)
                        break
                except httpx.HTTPError:
                    continue

        # Respect max_pages limit
        if len(urls) > self.config.max_pages_per_site:
            urls = urls[:self.config.max_pages_per_site]

        return urls

    def _parse_sitemap(self, xml_content: str) -> List[str]:
        """Parse sitemap XML and extract URLs"""
        try:
            root = ET.fromstring(xml_content)

            # Handle namespace
            namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

            # Extract all <loc> tags
            urls = []
            for url_elem in root.findall('.//ns:loc', namespace):
                if url_elem.text:
                    urls.append(url_elem.text)

            # If no namespaced elements, try without namespace
            if not urls:
                for url_elem in root.findall('.//loc'):
                    if url_elem.text:
                        urls.append(url_elem.text)

            return urls

        except ET.ParseError as e:
            raise ValueError(f"Failed to parse sitemap XML: {e}")

    async def list_files(self) -> List[FileInfo]:
        """List all pages from sitemap as FileInfo objects"""
        urls = await self.get_sitemap_urls()

        files = []
        for url in urls:
            file_info = FileInfo(
                path=url,
                url=url,
                size=0,
                sha="",
                language="html"
            )
            files.append(file_info)

        return files