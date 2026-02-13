"""Data models for the Victus confidence subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal


ConfidenceEventType = Literal[
    "accept",
    "confirm",
    "success",
    "reject",
    "override",
    "failure",
    "clarify",
]


@dataclass(frozen=True)
class ConfidenceScore:
    """Represents a confidence score for a namespaced key."""

    key: str
    value: float
    updated_at: datetime
    samples: int


@dataclass(frozen=True)
class ConfidenceEvent:
    """Represents a confidence event used to update a score."""

    key: str
    event_type: ConfidenceEventType
    weight: float
    occurred_at: datetime
    meta: dict[str, Any] = field(default_factory=dict)
