import pytest

from kb.sources.github_git import GitHubRepoCloner


@pytest.mark.asyncio
async def test_list_files_includes_root_level_files(tmp_path):
    (tmp_path / "README").write_text("root readme", encoding="utf-8")
    (tmp_path / "README.md").write_text("markdown readme", encoding="utf-8")
    (tmp_path / "main.py").write_text("print('hello')", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "guide.md").write_text("guide", encoding="utf-8")

    cloner = GitHubRepoCloner("owner/repo")
    cloner.repo_path = tmp_path

    files = await cloner.list_files()
    indexed_paths = sorted(file.path for file in files)

    assert "README" in indexed_paths
    assert "README.md" in indexed_paths
    assert "main.py" in indexed_paths
    assert "docs/guide.md" in indexed_paths


@pytest.mark.asyncio
async def test_list_files_excludes_hidden_and_ignored_paths(tmp_path):
    (tmp_path / ".env").write_text("secret", encoding="utf-8")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "index.js").write_text("console.log('x')", encoding="utf-8")
    (tmp_path / "visible.md").write_text("visible", encoding="utf-8")

    cloner = GitHubRepoCloner("owner/repo")
    cloner.repo_path = tmp_path

    files = await cloner.list_files()
    indexed_paths = {file.path for file in files}

    assert ".env" not in indexed_paths
    assert "node_modules/index.js" not in indexed_paths
    assert "visible.md" in indexed_paths
