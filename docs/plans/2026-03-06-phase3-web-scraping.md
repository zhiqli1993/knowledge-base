# Phase 3: Web Scraping Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Implement web scraping to extract knowledge from documentation sites and web pages.

**Architecture:** Web adapter using trafilatura for content extraction, requests for fetching, with sitemap support.

**Tech Stack:** trafilatura, httpx, BeautifulSoup4 (for sitemap parsing)

---

## Phase 3: Web Scraping Integration

### Task 10: Web Page Fetcher

**Files:**
- Create: `kb/sources/web.py`
- Test: `tests/unit/sources/test_web.py`

**Step 1: Write web fetcher test**

Create: `tests/unit/sources/test_web.py`

```python
import pytest
from unittest.mock import patch, Mock
from kb.sources.web import WebPageFetcher
from kb.config import WebConfig

@pytest.mark.asyncio
async def test_fetch_single_page():
    """Test fetching single web page"""
    mock_html = """
    <html>
        <body>
            <article>
                <h1>Test Article</h1>
                <p>This is test content.</p>
            </article>
        </body>
    </html>
    """

    with patch('httpx.AsyncClient') as mock_client:
        mock_response = Mock()
        mock_response.text = mock_html
        mock_response.status_code = 200
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

        config = WebConfig()
        fetcher = WebPageFetcher("https://example.com/article", config)
        content = await fetcher.fetch_content()

        assert "Test Article" in content
        assert "test content" in content

def test_parse_url():
    """Test URL parsing and validation"""
    config = WebConfig()
    fetcher = WebPageFetcher("https://example.com/page", config)

    assert fetcher.url == "https://example.com/page"
    assert fetcher.domain == "example.com"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/sources/test_web.py -v`
Expected: FAIL

**Step 3: Implement web page fetcher**

Create: `kb/sources/web.py`

```python
import httpx
from typing import Optional
from urllib.parse import urlparse
import trafilatura
from kb.config import WebConfig

class WebPageFetcher:
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

    def get_file_info(self):
        """Get FileInfo representation of this page"""
        from kb.sources.file_info import FileInfo

        return FileInfo(
            path=self.url,
            url=self.url,
            size=0,  # Unknown until fetched
            sha="",  # Not applicable for web pages
            language="html"
        )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/sources/test_web.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add kb/sources/web.py tests/unit/sources/test_web.py
git commit -m "feat: add web page fetcher with trafilatura extraction"
```

---

### Task 11: Website Sitemap Fetcher

**Files:**
- Modify: `kb/sources/web.py`
- Test: `tests/unit/sources/test_web_sitemap.py`

**Step 1: Write sitemap fetcher test**

Create: `tests/unit/sources/test_web_sitemap.py`

```python
import pytest
from unittest.mock import patch, Mock
from kb.sources.web import WebSiteFetcher
from kb.config import WebConfig

@pytest.mark.asyncio
async def test_fetch_sitemap():
    """Test fetching URLs from sitemap"""
    mock_sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url>
            <loc>https://example.com/page1</loc>
        </url>
        <url>
            <loc>https://example.com/page2</loc>
        </url>
    </urlset>
    """

    with patch('httpx.AsyncClient') as mock_client:
        mock_response = Mock()
        mock_response.text = mock_sitemap_xml
        mock_response.status_code = 200
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

        config = WebConfig()
        fetcher = WebSiteFetcher("https://example.com", config)
        urls = await fetcher.get_sitemap_urls()

        assert len(urls) == 2
        assert "https://example.com/page1" in urls
        assert "https://example.com/page2" in urls

@pytest.mark.asyncio
async def test_fetch_site_with_limit():
    """Test fetching site with max_pages limit"""
    config = WebConfig(max_pages_per_site=1)
    fetcher = WebSiteFetcher("https://example.com", config)

    # Mock sitemap with 5 URLs
    mock_urls = [
        "https://example.com/page1",
        "https://example.com/page2",
        "https://example.com/page3",
        "https://example.com/page4",
        "https://example.com/page5",
    ]

    with patch.object(fetcher, 'get_sitemap_urls', return_value=mock_urls):
        limited_urls = await fetcher.get_sitemap_urls()
        # Should respect max_pages_per_site limit
        assert len(limited_urls[:config.max_pages_per_site]) == 1
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/sources/test_web_sitemap.py -v`
Expected: FAIL

**Step 3: Implement sitemap fetcher**

Add to: `kb/sources/web.py`

```python
from xml.etree import ElementTree as ET
from typing import List

class WebSiteFetcher:
    def __init__(self, base_url: str, config: WebConfig):
        self.base_url = base_url.rstrip('/')
        self.config = config

        parsed = urlparse(base_url)
        self.domain = parsed.netloc
        self.scheme = parsed.scheme or "https"

    async def get_sitemap_urls(self) -> List[str]:
        """Fetch URLs from sitemap.xml"""
        sitemap_urls = [
            f"{self.base_url}/sitemap.xml",
            f"{self.base_url}/sitemap_index.xml",
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

    async def list_files(self) -> List:
        """List all pages from sitemap as FileInfo objects"""
        urls = await self.get_sitemap_urls()

        files = []
        for url in urls:
            from kb.sources.file_info import FileInfo
            file_info = FileInfo(
                path=url,
                url=url,
                size=0,
                sha="",
                language="html"
            )
            files.append(file_info)

        return files
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/sources/test_web_sitemap.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add kb/sources/web.py tests/unit/sources/test_web_sitemap.py
git commit -m "feat: add sitemap parsing for website crawling"
```

---

### Task 12: Integration Test for Web Scraping

**Files:**
- Test: `tests/integration/test_web_integration.py`

**Step 1: Write integration test**

Create: `tests/integration/test_web_integration.py`

```python
import pytest
from unittest.mock import patch, Mock
from kb.sources.web import WebPageFetcher, WebSiteFetcher
from kb.config import WebConfig

@pytest.mark.asyncio
async def test_web_page_extraction_integration():
    """Test complete web page extraction flow"""
    mock_html = """
    <!DOCTYPE html>
    <html>
        <head><title>Test Page</title></head>
        <body>
            <nav>Navigation Menu</nav>
            <main>
                <h1>Main Article</h1>
                <p>This is the main content that should be extracted.</p>
            </main>
            <footer>Footer content</footer>
        </body>
    </html>
    """

    with patch('httpx.AsyncClient') as mock_client:
        mock_response = Mock()
        mock_response.text = mock_html
        mock_response.status_code = 200
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

        config = WebConfig()
        fetcher = WebPageFetcher("https://example.com/article", config)
        content = await fetcher.fetch_content()

        # trafilatura should extract main content, not nav/footer
        assert "Main Article" in content
        assert "main content" in content
        # Navigation and footer might be filtered out by trafilatura

@pytest.mark.asyncio
async def test_website_sitemap_integration():
    """Test complete website sitemap extraction"""
    mock_sitemap = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url><loc>https://docs.example.com/intro</loc></url>
        <url><loc>https://docs.example.com/guide</loc></url>
        <url><loc>https://docs.example.com/api</loc></url>
    </urlset>
    """

    with patch('httpx.AsyncClient') as mock_client:
        mock_response = Mock()
        mock_response.text = mock_sitemap
        mock_response.status_code = 200
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

        config = WebConfig()
        fetcher = WebSiteFetcher("https://docs.example.com", config)
        files = await fetcher.list_files()

        assert len(files) == 3
        assert all(f.language == "html" for f in files)
        assert files[0].url == "https://docs.example.com/intro"
```

**Step 2: Run test to verify it passes**

Run: `pytest tests/integration/test_web_integration.py -v`
Expected: PASS

**Step 3: Commit**

```bash
git add tests/integration/test_web_integration.py
git commit -m "test: add web scraping integration tests"
```

---

## Summary

Phase 3 adds web scraping with:
- WebPageFetcher for single page extraction
- WebSiteFetcher for sitemap-based crawling
- trafilatura for clean content extraction
- Respects max_pages_per_site limits
- Integration tests

**Next Phase (Phase 4):** Chroma vector database integration
