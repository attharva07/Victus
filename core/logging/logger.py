from __future__ import annotations

import re
import logging
from typing import Any, Optional

from core.config import get_security_config


_LOGGER: Optional[logging.Logger] = None
_SECRET_FIELD_NAMES = {"token", "secret", "password", "api_key", "authorization", "credential", "key"}
_SECRET_PATTERNS = [
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    re.compile(r"\b(?:api[_-]?key|token|password|secret|authorization)\s*[:=]\s*[^\s,;]+", re.IGNORECASE),
    re.compile(r"\b(?:bearer\s+)[A-Za-z0-9._\-]+", re.IGNORECASE),
]


def get_logger() -> logging.Logger:
    global _LOGGER
    if _LOGGER is None:
        logger = logging.getLogger("victus")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s %(levelname)s %(name)s %(message)s",
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        _LOGGER = logger
    return _LOGGER


def _redact_string(value: str) -> str:
    redacted = value
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def _redact_value(key: str, value: Any, enabled: bool) -> Any:
    if not enabled:
        return value
    key_l = key.lower()
    if key_l in _SECRET_FIELD_NAMES:
        return "[REDACTED]"
    if isinstance(value, str):
        return _redact_string(value)
    if isinstance(value, dict):
        return {k: _redact_value(str(k), v, enabled) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact_value(key, item, enabled) for item in value]
    return value


def log_event(event: str, **fields: Any) -> None:
    logger = get_logger()
    config = get_security_config()
    payload = {"event": event}
    payload.update(redact_fields(fields, enabled=config.log_redaction_enabled))
    logger.info("%s", payload)


def redact_fields(fields: dict[str, Any], *, enabled: bool) -> dict[str, Any]:
    return {key: _redact_value(key, value, enabled) for key, value in fields.items()}
