from __future__ import annotations

from dataclasses import dataclass


@dataclass
class UpdateInfo:
    available: bool
    version: str | None = None


def check_updates() -> UpdateInfo:
    """Placeholder for update checks."""
    return UpdateInfo(available=False)


def download_update() -> None:
    """Placeholder for downloading updates."""
    return None


def apply_update_on_restart() -> None:
    """Placeholder for staging updates on restart."""
    return None
