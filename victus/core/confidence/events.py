"""Event schema helpers for deterministic confidence updates."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .models import ConfidenceEvent, ConfidenceEventType

POSITIVE_EVENT_TYPES: set[ConfidenceEventType] = {"accept", "confirm", "success"}
NEGATIVE_EVENT_TYPES: set[ConfidenceEventType] = {"reject", "override", "failure", "clarify"}


def utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""

    return datetime.now(timezone.utc)


def ensure_utc(ts: datetime) -> datetime:
    """Normalize a datetime to timezone-aware UTC."""

    if ts.tzinfo is None:
        return ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def normalize_event(
    key: str,
    event_type: ConfidenceEventType,
    weight: float = 1.0,
    occurred_at: datetime | None = None,
    meta: dict[str, Any] | None = None,
) -> ConfidenceEvent:
    """Build a normalized confidence event with UTC timestamp and positive weight."""

    ts = ensure_utc(occurred_at or utc_now())
    normalized_weight = max(0.0, float(weight))
    return ConfidenceEvent(
        key=key,
        event_type=event_type,
        weight=normalized_weight,
        occurred_at=ts,
        meta=meta or {},
    )


def is_positive(event_type: ConfidenceEventType) -> bool:
    """Return True when an event type should increase confidence."""

    return event_type in POSITIVE_EVENT_TYPES


def is_negative(event_type: ConfidenceEventType) -> bool:
    """Return True when an event type should decrease confidence."""

    return event_type in NEGATIVE_EVENT_TYPES
