import pytest
from unittest.mock import patch, Mock, AsyncMock
from mcp_server.sources.web import WebSiteFetcher
from mcp_server.config import WebConfig


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

        mock_client_instance = AsyncMock()
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(return_value=mock_response)

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

    # Mock both the HTTP client and the parse method
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = ""

    with patch('httpx.AsyncClient') as mock_client:
        mock_client_instance = AsyncMock()
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(return_value=mock_response)

        with patch.object(fetcher, '_parse_sitemap', return_value=mock_urls):
            urls = await fetcher.get_sitemap_urls()
            # Should respect max_pages_per_site limit
            assert len(urls) == 1


@pytest.mark.asyncio
async def test_sitemap_fallback():
    """Test fallback from sitemap_index.xml to sitemap.xml"""
    mock_sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url>
            <loc>https://example.com/fallback</loc>
        </url>
    </urlset>
    """

    call_count = 0

    async def mock_get(url):
        nonlocal call_count
        call_count += 1
        if "sitemap_index" in url:
            # First URL returns 404
            response = Mock()
            response.status_code = 404
            return response
        else:
            # Second URL returns content
            response = Mock()
            response.text = mock_sitemap_xml
            response.status_code = 200
            return response

    with patch('httpx.AsyncClient') as mock_client:
        mock_client_instance = AsyncMock()
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = mock_get

        config = WebConfig()
        fetcher = WebSiteFetcher("https://example.com", config)
        urls = await fetcher.get_sitemap_urls()

        assert len(urls) == 1
        assert "https://example.com/fallback" in urls
        assert call_count == 2


def test_parse_sitemap_xml():
    """Test parsing sitemap XML content"""
    config = WebConfig()
    fetcher = WebSiteFetcher("https://example.com", config)

    xml_with_namespace = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url>
            <loc>https://example.com/page1</loc>
        </url>
        <url>
            <loc>https://example.com/page2</loc>
        </url>
    </urlset>
    """

    urls = fetcher._parse_sitemap(xml_with_namespace)

    assert len(urls) == 2
    assert "https://example.com/page1" in urls
    assert "https://example.com/page2" in urls


def test_parse_sitemap_without_namespace():
    """Test parsing sitemap XML without namespace"""
    config = WebConfig()
    fetcher = WebSiteFetcher("https://example.com", config)

    xml_without_namespace = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset>
        <url>
            <loc>https://example.com/page1</loc>
        </url>
        <url>
            <loc>https://example.com/page2</loc>
        </url>
    </urlset>
    """

    urls = fetcher._parse_sitemap(xml_without_namespace)

    assert len(urls) == 2
    assert "https://example.com/page1" in urls
    assert "https://example.com/page2" in urls


@pytest.mark.asyncio
async def test_list_files():
    """Test listing files from sitemap as FileInfo objects"""
    config = WebConfig()
    fetcher = WebSiteFetcher("https://example.com", config)

    mock_urls = [
        "https://example.com/page1",
        "https://example.com/page2",
    ]

    with patch.object(fetcher, 'get_sitemap_urls', return_value=mock_urls):
        files = await fetcher.list_files()

        assert len(files) == 2
        assert files[0].url == "https://example.com/page1"
        assert files[0].path == "https://example.com/page1"
        assert files[1].url == "https://example.com/page2"
        assert files[1].path == "https://example.com/page2"


def test_base_url_parsing():
    """Test base URL parsing and normalization"""
    config = WebConfig()

    fetcher = WebSiteFetcher("https://example.com", config)
    assert fetcher.base_url == "https://example.com"
    assert fetcher.domain == "example.com"
    assert fetcher.scheme == "https"

    # Test trailing slash removal
    fetcher2 = WebSiteFetcher("https://example.com/", config)
    assert fetcher2.base_url == "https://example.com"