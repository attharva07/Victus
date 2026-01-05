"""Helpers to keep failure logs free of sensitive data."""

from __future__ import annotations

import hashlib
import re
import traceback
from typing import Any, Dict, Optional


SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{16,}", re.IGNORECASE),
    re.compile(r"api[_-]?key[:=]\s*[^\s]+", re.IGNORECASE),
    re.compile(r"bearer\s+[A-Za-z0-9\-_.~+/]+=*", re.IGNORECASE),
    re.compile(r"[A-Fa-f0-9]{32,}"),
]


def redact_args(args: Dict[str, Any]) -> Dict[str, Any]:
    """Drop all arguments; callers mark ``args_redacted=True`` in the event."""

    _ = args  # Explicitly ignore
    return {}


def safe_user_intent(text: str) -> str:
    """Trim user intent and scrub obvious secrets."""

    cleaned = text.replace("\n", " ").strip()
    for pattern in SECRET_PATTERNS:
        cleaned = pattern.sub("[REDACTED]", cleaned)
    return cleaned[:200]


def hash_stack(exc: Exception) -> Optional[str]:
    """Hash the exception type and top stack frame without storing the full trace."""

    tb = exc.__traceback__
    if not tb:
        return None

    frames = traceback.extract_tb(tb)
    if not frames:
        return None

    top = frames[-1]
    digest_source = f"{exc.__class__.__name__}:{top.filename}:{top.name}:{top.lineno}"
    return hashlib.sha256(digest_source.encode("utf-8")).hexdigest()
