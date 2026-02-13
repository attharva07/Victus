"""Helpers for generating namespaced confidence keys."""

from __future__ import annotations

_VALID_NAMESPACES = {"router", "ui"}


def make_key(namespace: str, *parts: str) -> str:
    """Create a confidence key in `<namespace>.<part>...` format."""

    if namespace not in _VALID_NAMESPACES:
        raise ValueError(f"Unsupported confidence namespace: {namespace}")
    cleaned_parts = [part.strip() for part in parts if part and part.strip()]
    if not cleaned_parts:
        raise ValueError("At least one key segment is required")
    return ".".join([namespace, *cleaned_parts])


def validate_key(key: str) -> None:
    """Validate that a confidence key uses a known namespace."""

    namespace, _, remainder = key.partition(".")
    if namespace not in _VALID_NAMESPACES or not remainder:
        raise ValueError(
            "Confidence keys must be namespaced and start with 'router.' or 'ui.'",
        )
