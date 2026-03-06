import pytest
from unittest.mock import Mock, patch, MagicMock
from mcp_server.sources.github import GitHubRepoFetcher
from mcp_server.config import GitHubConfig

@pytest.mark.asyncio
async def test_github_fetcher_integration():
    """Test GitHub fetcher with mocked API"""

    # Mock file content objects
    mock_readme = MagicMock()
    mock_readme.type = 'file'
    mock_readme.path = 'README.md'
    mock_readme.html_url = 'https://github.com/owner/repo/blob/main/README.md'
    mock_readme.size = 1024
    mock_readme.sha = 'abc123'
    mock_readme.decoded_content = b'# Test README'

    mock_node_modules = MagicMock()
    mock_node_modules.type = 'file'
    mock_node_modules.path = 'node_modules/package.json'
    mock_node_modules.html_url = 'https://github.com/owner/repo/blob/main/node_modules/package.json'
    mock_node_modules.size = 512
    mock_node_modules.sha = 'def456'
    mock_node_modules.decoded_content = b'{}'

    # Mock GitHub API
    mock_repo = MagicMock()
    mock_repo.get_contents.return_value = [mock_readme, mock_node_modules]

    with patch('mcp_server.sources.github.Github') as mock_github_class:
        mock_github_instance = MagicMock()
        mock_github_instance.get_repo.return_value = mock_repo
        mock_github_class.return_value = mock_github_instance

        config = GitHubConfig()
        fetcher = GitHubRepoFetcher("owner/repo", config)
        files = await fetcher.list_files()

        # Should include README.md but exclude node_modules
        assert len(files) == 1
        assert files[0].path == 'README.md'
        assert files[0].language == 'markdown'

@pytest.mark.asyncio
async def test_github_fetcher_with_directories():
    """Test GitHub fetcher handles directories correctly"""

    # Mock directory
    mock_src_dir = MagicMock()
    mock_src_dir.type = 'dir'
    mock_src_dir.path = 'src'

    # Mock file in src directory
    mock_index = MagicMock()
    mock_index.type = 'file'
    mock_index.path = 'src/index.ts'
    mock_index.html_url = 'https://github.com/owner/repo/blob/main/src/index.ts'
    mock_index.size = 2048
    mock_index.sha = 'xyz789'
    mock_index.decoded_content = b'console.log("hello");'

    mock_repo = MagicMock()
    # First call returns directory, second call returns file in directory
    mock_repo.get_contents.side_effect = [
        [mock_src_dir],  # Root level
        [mock_index]     # src/ directory
    ]

    with patch('mcp_server.sources.github.Github') as mock_github_class:
        mock_github_instance = MagicMock()
        mock_github_instance.get_repo.return_value = mock_repo
        mock_github_class.return_value = mock_github_instance

        config = GitHubConfig()
        fetcher = GitHubRepoFetcher("owner/repo", config)
        files = await fetcher.list_files()

        assert len(files) == 1
        assert files[0].path == 'src/index.ts'
        assert files[0].language == 'typescript'