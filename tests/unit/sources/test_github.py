import pytest
from kb.sources.github import GitHubRepoFetcher
from kb.config import GitHubConfig

def test_parse_repo_url():
    """Test parsing GitHub repo URL"""
    config = GitHubConfig()
    fetcher = GitHubRepoFetcher("https://github.com/owner/repo", config)

    assert fetcher.owner == "owner"
    assert fetcher.repo_name == "repo"

def test_parse_short_repo_url():
    """Test parsing short GitHub repo format"""
    config = GitHubConfig()
    fetcher = GitHubRepoFetcher("owner/repo", config)

    assert fetcher.owner == "owner"
    assert fetcher.repo_name == "repo"

def test_should_include_file():
    """Test file inclusion logic"""
    config = GitHubConfig()
    fetcher = GitHubRepoFetcher("owner/repo", config)

    # Default includes
    assert fetcher.should_include("README.md") is True
    assert fetcher.should_include("docs/guide.md") is True
    assert fetcher.should_include("src/index.ts") is True

    # Default excludes
    assert fetcher.should_include("node_modules/package.json") is False
    assert fetcher.should_include("dist/bundle.js") is False