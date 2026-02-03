from __future__ import annotations

from pathlib import Path
from typing import Iterable

DEFAULT_ALLOWED_EXTENSIONS = {".txt", ".md", ".json", ".csv"}


class VaultPathError(ValueError):
    pass


def is_allowed_extension(path: Path, allowed_extensions: Iterable[str] = DEFAULT_ALLOWED_EXTENSIONS) -> bool:
    return path.suffix.lower() in {ext.lower() for ext in allowed_extensions}


def safe_join(base: Path, user_path: str) -> Path:
    base_path = base.resolve()
    candidate = Path(user_path)

    if candidate.is_absolute() or ".." in candidate.parts:
        raise VaultPathError("Invalid path traversal attempt")

    full_path = (base_path / candidate).resolve()
    if base_path != full_path and base_path not in full_path.parents:
        raise VaultPathError("Path escapes the vault")

    current = base_path
    for part in candidate.parts:
        current = current / part
        if current.exists() and current.is_symlink():
            resolved = current.resolve()
            if base_path != resolved and base_path not in resolved.parents:
                raise VaultPathError("Symlink escapes the vault")

    return full_path
