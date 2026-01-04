from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

from ..util.jsonl import append_jsonl, read_jsonl
from .models import FailureRecord

FAILURES_PATH = Path("data/failures/failures.jsonl")


def append_failure(record: Dict) -> None:
    append_jsonl(FAILURES_PATH, record)


def list_failures(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    since: Optional[int] = None,
    limit: Optional[int] = None,
) -> List[FailureRecord]:
    failures = [FailureRecord(**rec) for rec in read_jsonl(FAILURES_PATH)]
    if status:
        failures = [f for f in failures if f.status == status]
    if severity:
        failures = [f for f in failures if f.severity == severity]
    if since is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=since)
        failures = [f for f in failures if datetime.fromisoformat(f.timestamp) >= cutoff]
    if limit:
        failures = failures[-limit:]
    return failures


def get_failure(failure_id: str) -> Optional[FailureRecord]:
    for record in list_failures():
        if record.failure_id == failure_id:
            return record
    return None
