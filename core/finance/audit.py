from __future__ import annotations

from typing import Any

from core.logging.audit import audit_event, safe_excerpt, text_hash

SENSITIVE_FIELDS = {"notes", "note"}


def _redact_field(key: str, value: Any) -> Any:
    if value is None:
        return None
    if key in SENSITIVE_FIELDS and isinstance(value, str):
        return {"excerpt": safe_excerpt(value, max_len=24), "sha256": text_hash(value)}
    return value


def finance_audit(event: str, **fields: Any) -> None:
    sanitized = {key: _redact_field(key, value) for key, value in fields.items()}
    audit_event(event, **sanitized)
