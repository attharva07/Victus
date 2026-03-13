from __future__ import annotations

from typing import Any

from core.logging.logger import redact_fields


def sanitize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Sanitize sensitive values for logs/audit trails."""
    return redact_fields(payload, enabled=True)
