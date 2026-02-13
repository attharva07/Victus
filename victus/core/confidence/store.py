"""JSON-backed persistence for confidence scores and event audit history."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .events import ensure_utc
from .keys import validate_key
from .models import ConfidenceEvent, ConfidenceScore

DEFAULT_CONFIDENCE_STORE_PATH = Path("victus/data/confidence/store.json")


class ConfidenceStore:
    """Persistent confidence store with deterministic defaults."""

    def __init__(self, path: Path = DEFAULT_CONFIDENCE_STORE_PATH) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.save({"scores": {}, "events": []})

    def load(self) -> dict[str, Any]:
        """Load raw store payload from disk."""

        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, payload: dict[str, Any]) -> None:
        """Persist raw store payload to disk."""

        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_score(self, key: str) -> ConfidenceScore:
        """Return score for key, creating a default score of 0.5 if missing."""

        validate_key(key)
        data = self.load()
        raw_score = data.setdefault("scores", {}).get(key)
        if raw_score is None:
            score = ConfidenceScore(
                key=key,
                value=0.5,
                updated_at=datetime.now(timezone.utc),
                samples=0,
            )
            data["scores"][key] = _serialize_score(score)
            self.save(data)
            return score
        return _deserialize_score(raw_score)

    def update_score(self, key: str, new_value: float) -> ConfidenceScore:
        """Update a score and increment its sample count."""

        validate_key(key)
        current = self.get_score(key)
        updated = ConfidenceScore(
            key=key,
            value=float(new_value),
            updated_at=datetime.now(timezone.utc),
            samples=current.samples + 1,
        )
        data = self.load()
        data.setdefault("scores", {})[key] = _serialize_score(updated)
        self.save(data)
        return updated

    def append_event(self, event: ConfidenceEvent) -> None:
        """Persist a confidence event in the audit log."""

        validate_key(event.key)
        data = self.load()
        data.setdefault("events", []).append(_serialize_event(event))
        self.save(data)


def _serialize_score(score: ConfidenceScore) -> dict[str, Any]:
    raw = asdict(score)
    raw["updated_at"] = ensure_utc(score.updated_at).isoformat()
    return raw


def _deserialize_score(raw: dict[str, Any]) -> ConfidenceScore:
    return ConfidenceScore(
        key=str(raw["key"]),
        value=float(raw["value"]),
        updated_at=ensure_utc(datetime.fromisoformat(str(raw["updated_at"]))),
        samples=int(raw["samples"]),
    )


def _serialize_event(event: ConfidenceEvent) -> dict[str, Any]:
    raw = asdict(event)
    raw["occurred_at"] = ensure_utc(event.occurred_at).isoformat()
    return raw
