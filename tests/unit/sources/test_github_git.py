from unittest.mock import Mock, patch

import pytest

from kb.sources.github_git import GitHubRepoCloner


@pytest.mark.asyncio
async def test_list_files_includes_root_level_files(tmp_path):
    (tmp_path / "README").write_text("root readme", encoding="utf-8")
    (tmp_path / "README.md").write_text("markdown readme", encoding="utf-8")
    (tmp_path / "main.py").write_text("print('hello')", encoding="utf-8")
    (tmp_path / "kubectl.yaml").write_text("apiVersion: v1", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "guide.md").write_text("guide", encoding="utf-8")

    cloner = GitHubRepoCloner("owner/repo")
    cloner.repo_path = tmp_path

    files = await cloner.list_files()
    indexed_paths = sorted(file.path for file in files)

    assert "README" in indexed_paths
    assert "README.md" in indexed_paths
    assert "main.py" in indexed_paths
    assert "kubectl.yaml" in indexed_paths
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


def test_detect_default_branch_parses_head_ref():
    completed = Mock(returncode=0, stdout="ref: refs/heads/tekton\tHEAD\nabc\tHEAD\n", stderr="")

    with patch("kb.sources.github_git.subprocess.run", return_value=completed) as mock_run:
        branch = GitHubRepoCloner.detect_default_branch("https://github-cli.corp.ebay.com/org/repo")

    assert branch == "tekton"
    mock_run.assert_called_once()


def test_detect_default_branch_normalizes_short_repo():
    completed = Mock(returncode=0, stdout="ref: refs/heads/main\tHEAD\nabc\tHEAD\n", stderr="")

    with patch("kb.sources.github_git.subprocess.run", return_value=completed) as mock_run:
        branch = GitHubRepoCloner.detect_default_branch("owner/repo")

    assert branch == "main"
    cmd = mock_run.call_args.args[0]
    assert cmd[:3] == ["git", "ls-remote", "--symref"]
    assert cmd[3] == "https://github.com/owner/repo.git"
