import re
from typing import Tuple

from .models import ALLOWED_CATEGORIES


_DENYLIST_PATTERNS = [
    re.compile(r"\bI felt\b", re.IGNORECASE),
    re.compile(r"\bdepressed\b", re.IGNORECASE),
    re.compile(r"\banxious\b", re.IGNORECASE),
    re.compile(r"\brain dump\b", re.IGNORECASE),
    re.compile(r"\btranscript\b", re.IGNORECASE),
    re.compile(r"\btoday\b", re.IGNORECASE),
    re.compile(r"\btomorrow\b", re.IGNORECASE),
]


def validate_category(category: str) -> bool:
    return category in ALLOWED_CATEGORIES


def detect_denied_content(content: str) -> Tuple[bool, str]:
    for pattern in _DENYLIST_PATTERNS:
        if pattern.search(content):
            return True, f"Content matches denylist pattern: {pattern.pattern}"
    return False, ""


def validate_memory_proposal(category: str, content: str) -> Tuple[bool, str]:
    if not validate_category(category):
        return False, "Category is not allowed"
    denied, reason = detect_denied_content(content)
    if denied:
        return False, reason
    return True, ""
