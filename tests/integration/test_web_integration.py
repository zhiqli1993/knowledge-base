import pytest
from unittest.mock import patch, Mock, AsyncMock
from mcp_server.sources.web import WebPageFetcher, WebSiteFetcher
from mcp_server.config import WebConfig


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
        mock_response.raise_for_status = Mock()

        mock_client_instance = AsyncMock()
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(return_value=mock_response)

        config = WebConfig()
        fetcher = WebPageFetcher("https://example.com/article", config)
        content = await fetcher.fetch_content()

        # trafilatura should extract main content, not nav/footer
        assert "Main Article" in content
        assert "main content" in content


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

        mock_client_instance = AsyncMock()
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(return_value=mock_response)

        config = WebConfig()
        fetcher = WebSiteFetcher("https://docs.example.com", config)
        files = await fetcher.list_files()

        assert len(files) == 3
        assert all(f.language == "html" for f in files)
        assert files[0].url == "https://docs.example.com/intro"


@pytest.mark.asyncio
async def test_website_fetcher_with_empty_sitemap():
    """Test website fetcher handles empty sitemap gracefully"""
    mock_empty_sitemap = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    </urlset>
    """

    with patch('httpx.AsyncClient') as mock_client:
        mock_response = Mock()
        mock_response.text = mock_empty_sitemap
        mock_response.status_code = 200

        mock_client_instance = AsyncMock()
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(return_value=mock_response)

        config = WebConfig()
        fetcher = WebSiteFetcher("https://docs.example.com", config)
        files = await fetcher.list_files()

        assert len(files) == 0


@pytest.mark.asyncio
async def test_website_fetcher_fallback_on_error():
    """Test website fetcher handles sitemap fetch errors"""
    import httpx

    with patch('httpx.AsyncClient') as mock_client:
        mock_client_instance = AsyncMock()
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(side_effect=httpx.HTTPError("Not found"))

        config = WebConfig()
        fetcher = WebSiteFetcher("https://docs.example.com", config)
        files = await fetcher.list_files()

        # Should return empty list on error, not raise exception
        assert len(files) == 0