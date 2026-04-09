import pytest
from unittest.mock import patch, Mock, AsyncMock
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
        mock_response.raise_for_status = Mock()

        # Setup async context manager
        mock_client_instance = AsyncMock()
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(return_value=mock_response)

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


def test_parse_url_without_scheme():
    """Test URL parsing with missing scheme adds https"""
    config = WebConfig()
    fetcher = WebPageFetcher("example.com/page", config)

    assert fetcher.url == "https://example.com/page"
    assert fetcher.scheme == "https"