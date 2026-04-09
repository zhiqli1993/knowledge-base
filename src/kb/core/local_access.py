"""Helpers for local filesystem access policy."""
from pathlib import Path
from typing import Iterable

from kb.config import LocalConfig


def get_allowed_roots(config: LocalConfig, fallback_root: Path | None = None) -> list[Path]:
    """Resolve allowed roots for local indexing."""
    if config.allow_unrestricted_paths:
        return []

    roots = config.allowed_paths_expanded
    if roots:
        return roots

    if fallback_root is not None:
        return [fallback_root.expanduser().resolve()]

    return []


def is_path_allowed(path: Path, allowed_roots: Iterable[Path], allow_unrestricted: bool) -> bool:
    """Return whether a path falls under one of the allowed roots."""
    if allow_unrestricted:
        return True

    resolved_path = path.expanduser().resolve()
    for root in allowed_roots:
        try:
            resolved_path.relative_to(root)
            return True
        except ValueError:
            continue

    return False
