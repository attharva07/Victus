from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ApiKeyRecord:
    name: str
    key_id: str
    hashed_secret: str


def list_api_keys() -> list[ApiKeyRecord]:
    """Placeholder for future API key management."""
    return []
