from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from core.config import get_logs_dir


@dataclass
class AuditEvent:
    event_type: str
    actor: str
    resource: str
    result: str
    metadata: Optional[dict[str, Any]] = None


_audit_logger = logging.getLogger("victus.audit")


def setup_audit_logger() -> None:
    if _audit_logger.handlers:
        return

    log_file = get_logs_dir() / "audit.log"
    handler = logging.FileHandler(log_file)
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)

    _audit_logger.setLevel(logging.INFO)
    _audit_logger.addHandler(handler)


def log_event(event: AuditEvent) -> None:
    setup_audit_logger()
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event.event_type,
        "actor": event.actor,
        "resource": event.resource,
        "result": event.result,
        "metadata": event.metadata or {},
    }
    _audit_logger.info(payload)
