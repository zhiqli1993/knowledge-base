from mcp_server.sources.file_info import FileInfo

def test_file_info_creation():
    """Test FileInfo model creation"""
    file_info = FileInfo(
        path="src/index.ts",
        url="https://github.com/owner/repo/blob/main/src/index.ts",
        size=1024,
        sha="abc123",
        language="typescript"
    )
    assert file_info.path == "src/index.ts"
    assert file_info.language == "typescript"

def test_file_info_from_github_content():
    """Test creating FileInfo from GitHub ContentFile"""
    # Mock GitHub ContentFile structure
    mock_content = type('obj', (object,), {
        'path': 'README.md',
        'html_url': 'https://github.com/owner/repo/blob/main/README.md',
        'size': 2048,
        'sha': 'def456'
    })()

    file_info = FileInfo.from_github_content(mock_content, 'owner/repo')
    assert file_info.path == 'README.md'
    assert file_info.size == 2048