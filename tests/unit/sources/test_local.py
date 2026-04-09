import os

import pytest

from kb.sources.local import LocalFileCollector


def test_local_collector_includes_root_level_files(tmp_path):
    """Default include globs should match files at the source root."""
    (tmp_path / "README.md").write_text("# Root readme", encoding="utf-8")
    nested_docs = tmp_path / "docs"
    nested_docs.mkdir()
    (nested_docs / "guide.md").write_text("# Guide", encoding="utf-8")

    collector = LocalFileCollector(
        source_path=str(tmp_path),
        include=["**/*.md", "**/README*"],
        exclude=[],
    )

    files = [file_path.relative_to(tmp_path).as_posix() for file_path in collector._iter_files()]
    assert "README.md" in files
    assert "docs/guide.md" in files


@pytest.mark.asyncio
async def test_local_collector_skips_symlink_outside_allowed_roots(tmp_path):
    """Symlinked files must not escape the approved local roots."""
    if not hasattr(os, "symlink"):
        pytest.skip("symlinks are not supported on this platform")

    allowed_root = tmp_path / "allowed"
    outside_root = tmp_path / "outside"
    allowed_root.mkdir()
    outside_root.mkdir()

    secret_file = outside_root / "secret.md"
    secret_file.write_text("secret", encoding="utf-8")

    symlink_path = allowed_root / "secret-link.md"
    symlink_path.symlink_to(secret_file)

    collector = LocalFileCollector(
        source_path=str(allowed_root),
        include=["**/*.md"],
        exclude=[],
        allowed_roots=[allowed_root.resolve()],
        allow_unrestricted=False,
    )

    files = await collector.list_files()
    assert files == []
