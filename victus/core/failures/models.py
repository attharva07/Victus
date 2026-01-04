from dataclasses import dataclass
from typing import Dict, Optional


SEVERITIES = {"low", "medium", "high"}
STATUSES = {"unresolved", "resolved", "deferred"}


@dataclass
class FailureRecord:
    failure_id: str
    timestamp: str
    context: str
    what_failed: str
    why_it_failed: str
    expected_behavior: str
    severity: str
    status: str
    links: Dict[str, Optional[str]]
