"""Standardized failure event schema (v1)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid


COMPONENTS = {"policy", "router", "executor", "tool", "parser", "memory"}
SEVERITIES = {"low", "medium", "high", "critical"}
CATEGORIES = {"policy_violation", "tool_error", "validation_error", "runtime_error", "unknown"}
RESOLUTION_STATUSES = {"new", "in_review", "resolved", "wont_fix"}


def _uuid() -> str:
    return str(uuid.uuid4())


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class FailureEvent:
    """Schema v1 failure event."""

    schema_version: str = "1.0"
    event_id: str = field(default_factory=_uuid)
    ts: str = field(default_factory=_iso_now)
    stage: str = "2"
    phase: str = "1"
    domain: str = "unknown"
    component: str = "executor"
    severity: str = "medium"
    category: str = "runtime_error"
    request_id: str = ""
    user_intent: str = ""
    action: Dict[str, Any] = field(default_factory=lambda: {"name": "", "args_redacted": True})
    failure: Dict[str, Any] = field(
        default_factory=lambda: {
            "code": "",
            "message": "",
            "exception_type": None,
            "stack_hash": None,
            "details_redacted": True,
        }
    )
    expected_behavior: str = ""
    remediation_hint: Optional[str] = None
    resolution: Dict[str, Any] = field(
        default_factory=lambda: {
            "status": "new",
            "resolved_ts": None,
            "notes": None,
        }
    )
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable mapping with enforced keys."""

        data = asdict(self)

        if self.component not in COMPONENTS:
            data["component"] = "executor"
        if self.severity not in SEVERITIES:
            data["severity"] = "medium"
        if self.category not in CATEGORIES:
            data["category"] = "unknown"
        resolution_status = data.get("resolution", {}).get("status")
        if resolution_status not in RESOLUTION_STATUSES:
            data["resolution"]["status"] = "new"

        return data

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "FailureEvent":
        """Create a ``FailureEvent`` from a dictionary, applying defaults."""

        return cls(**{**cls().to_dict(), **payload})
