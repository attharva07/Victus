"""Deterministic confidence scoring rules and façade API."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from .events import is_negative, is_positive
from .models import ConfidenceEvent, ConfidenceScore
from .store import ConfidenceStore

POSITIVE_STEP = 0.08
NEGATIVE_STEP = 0.14


class ConfidenceCore:
    """Apply confidence events and read scores using a backing store."""

    def __init__(self, store: ConfidenceStore, *, enable_decay: bool = False, decay_rate: float = 0.0) -> None:
        self._store = store
        self._enable_decay = enable_decay
        self._decay_rate = max(0.0, float(decay_rate))

    def get_score(self, key: str) -> ConfidenceScore:
        """Get the current score for a key."""

        score = self._store.get_score(key)
        if not self._enable_decay:
            return score
        decayed = _apply_decay(score, now=datetime.now(timezone.utc), decay_rate=self._decay_rate)
        if decayed.value == score.value:
            return score
        return self._store.update_score(key, decayed.value)

    def apply_event(self, event: ConfidenceEvent) -> ConfidenceScore:
        """Apply one event and return the updated score."""

        current = self._store.get_score(event.key)
        delta = _event_delta(event)
        updated_value = _clamp(current.value + delta)
        updated = self._store.update_score(event.key, updated_value)
        self._store.append_event(event)
        return updated

    def apply_events(self, events: Iterable[ConfidenceEvent]) -> dict[str, ConfidenceScore]:
        """Apply multiple events and return final updated score per key."""

        results: dict[str, ConfidenceScore] = {}
        for event in events:
            results[event.key] = self.apply_event(event)
        return results


def _event_delta(event: ConfidenceEvent) -> float:
    magnitude = abs(float(event.weight))
    if is_positive(event.event_type):
        return POSITIVE_STEP * magnitude
    if is_negative(event.event_type):
        return -NEGATIVE_STEP * magnitude
    return 0.0


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _apply_decay(score: ConfidenceScore, *, now: datetime, decay_rate: float) -> ConfidenceScore:
    """Optional time-based decay towards the neutral score of 0.5."""

    elapsed_hours = max(0.0, (now - score.updated_at).total_seconds() / 3600.0)
    if elapsed_hours <= 0 or decay_rate <= 0.0:
        return score
    direction = 0.5 - score.value
    adjusted = score.value + (direction * min(1.0, decay_rate * elapsed_hours))
    return ConfidenceScore(
        key=score.key,
        value=_clamp(adjusted),
        updated_at=score.updated_at,
        samples=score.samples,
    )
