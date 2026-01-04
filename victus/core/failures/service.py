from typing import Dict, Optional

from ..util.ids import generate_id
from ..util.time import now_iso
from .models import SEVERITIES, STATUSES
from .store import append_failure, get_failure, list_failures as store_list_failures


class FailureNotFound(Exception):
    pass


def log_failure(
    context: str,
    what_failed: str,
    why_it_failed: str,
    expected_behavior: str,
    severity: str = "medium",
    links: Optional[Dict[str, Optional[str]]] = None,
) -> str:
    if severity not in SEVERITIES:
        severity = "medium"
    failure_id = generate_id("fail")
    record = {
        "failure_id": failure_id,
        "timestamp": now_iso(),
        "context": context,
        "what_failed": what_failed,
        "why_it_failed": why_it_failed,
        "expected_behavior": expected_behavior,
        "severity": severity,
        "status": "unresolved",
        "links": links or {"trace_id": None, "module": None, "commit": None},
    }
    append_failure(record)
    return failure_id


def mark_status(failure_id: str, status: str) -> None:
    if status not in STATUSES:
        raise ValueError("Invalid status")
    record = get_failure(failure_id)
    if not record:
        raise FailureNotFound(failure_id)
    append_failure({**record.__dict__, "status": status})


def list_failures(status: str = None, severity: str = None, since: int = None, limit: int = None):
    return store_list_failures(status=status, severity=severity, since=since, limit=limit)
