from __future__ import annotations

import os
from pathlib import Path

DEFAULT_DATA_DIR_NAME = ".victus"


def get_data_dir() -> Path:
    """Return the Victus data directory, creating it if needed."""
    override = os.getenv("VICTUS_DATA_DIR")
    if override:
        data_dir = Path(override).expanduser()
    elif os.name == "nt":
        base = os.getenv("APPDATA")
        if not base:
            base = str(Path.home())
        data_dir = Path(base) / "Victus"
    else:
        data_dir = Path.home() / DEFAULT_DATA_DIR_NAME

    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_logs_dir() -> Path:
    logs_dir = get_data_dir() / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def get_vault_dir() -> Path:
    vault_dir = get_data_dir() / "vault"
    vault_dir.mkdir(parents=True, exist_ok=True)
    return vault_dir
