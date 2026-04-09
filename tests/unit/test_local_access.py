from pathlib import Path

from kb.config import LocalConfig
from kb.core.local_access import get_allowed_roots, is_path_allowed


def test_get_allowed_roots_uses_fallback_when_config_empty(tmp_path):
    config = LocalConfig()
    roots = get_allowed_roots(config, fallback_root=tmp_path)
    assert roots == [tmp_path.resolve()]


def test_is_path_allowed_accepts_child_of_allowed_root(tmp_path):
    allowed_root = tmp_path / "workspace"
    allowed_root.mkdir()
    target = allowed_root / "docs" / "guide.md"
    target.parent.mkdir()
    target.write_text("guide", encoding="utf-8")

    assert is_path_allowed(target, [allowed_root.resolve()], False) is True


def test_is_path_allowed_rejects_path_outside_allowed_root(tmp_path):
    allowed_root = tmp_path / "workspace"
    allowed_root.mkdir()
    other_root = tmp_path / "secret"
    other_root.mkdir()
    target = other_root / "notes.txt"
    target.write_text("secret", encoding="utf-8")

    assert is_path_allowed(target, [allowed_root.resolve()], False) is False
