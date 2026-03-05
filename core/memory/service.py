from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Iterable, Sequence
from uuid import uuid4

from core.config import get_security_config
from core.logging.audit import audit_event
from core.memory.store import DEFAULT_REPOSITORY, MemoryRepository

SENSITIVITY_LEVELS: tuple[str, ...] = ("public", "internal", "sensitive", "critical")
_SENSITIVITY_RANK = {name: idx for idx, name in enumerate(SENSITIVITY_LEVELS)}


class MemoryService:
    def __init__(self, repository: MemoryRepository | None = None) -> None:
        self.repository = repository or DEFAULT_REPOSITORY

    @staticmethod
    def _normalize_tags(tags: Iterable[str] | None) -> list[str]:
        if not tags:
            return []
        return [tag.strip() for tag in tags if tag and tag.strip()]

    @staticmethod
    def _normalize_sensitivity(sensitivity: str | None) -> str:
        normalized = (sensitivity or "internal").strip().lower()
        if normalized not in _SENSITIVITY_RANK:
            raise ValueError(f"Unsupported sensitivity level: {sensitivity}")
        return normalized

    def write(self, item: dict[str, object]) -> str:
        memory_id = str(item.get("id") or uuid4())
        ts = str(item.get("ts") or datetime.now(tz=timezone.utc).isoformat())
        content = str(item.get("content") or "").strip()
        if not content:
            raise ValueError("Memory content is required")

        sensitivity = self._normalize_sensitivity(item.get("sensitivity") if isinstance(item.get("sensitivity"), str) else None)
        record = {
            "id": memory_id,
            "ts": ts,
            "type": str(item.get("type") or "note"),
            "tags": json.dumps(self._normalize_tags(item.get("tags") if isinstance(item.get("tags"), list) else None)),
            "source": str(item.get("source") or "user"),
            "content": content,
            "importance": int(item.get("importance") or 5),
            "confidence": float(item.get("confidence") or 0.8),
            "sensitivity": sensitivity,
        }
        self.repository.add_memory(record)
        audit_event("memory_added", memory_id=memory_id, memory_type=record["type"], sensitivity=sensitivity)
        return memory_id

    def retrieve(
        self,
        query: str,
        *,
        max_items: int = 5,
        tags: Iterable[str] | None = None,
        allowed_sensitivity: Sequence[str] | None = None,
    ) -> list[dict[str, object]]:
        config = get_security_config()
        cap = min(max(1, max_items), config.max_memory_retrieval)
        normalized_tags = self._normalize_tags(tags)
        raw = self.repository.search_memories(query, normalized_tags, cap)
        filtered = self._filter_by_sensitivity(raw, allowed_sensitivity)
        audit_event("memory_searched", query=query, tags=normalized_tags, limit=cap, returned=len(filtered))
        return filtered

    def list_recent(
        self,
        *,
        max_items: int = 20,
        allowed_sensitivity: Sequence[str] | None = None,
    ) -> list[dict[str, object]]:
        config = get_security_config()
        cap = min(max(1, max_items), config.max_memory_retrieval)
        raw = self.repository.list_recent(cap)
        filtered = self._filter_by_sensitivity(raw, allowed_sensitivity)
        audit_event("memory_listed", limit=cap, returned=len(filtered))
        return filtered

    def get_by_id(self, memory_id: str, *, allowed_sensitivity: Sequence[str] | None = None) -> dict[str, object] | None:
        record = self.repository.get_by_id(memory_id)
        if record is None:
            return None
        filtered = self._filter_by_sensitivity([record], allowed_sensitivity)
        return filtered[0] if filtered else None

    def delete(self, memory_id: str) -> bool:
        deleted = self.repository.delete_memory(memory_id)
        audit_event("memory_deleted", memory_id=memory_id, deleted=deleted)
        return deleted

    def _filter_by_sensitivity(
        self,
        records: list[dict[str, object]],
        allowed_sensitivity: Sequence[str] | None,
    ) -> list[dict[str, object]]:
        max_allowed = self._max_allowed_rank(allowed_sensitivity)
        filtered: list[dict[str, object]] = []
        for record in records:
            record_level = self._normalize_sensitivity(str(record.get("sensitivity") or "internal"))
            if _SENSITIVITY_RANK[record_level] <= max_allowed:
                if "sensitivity" not in record:
                    record["sensitivity"] = record_level
                filtered.append(record)
        return filtered

    def _max_allowed_rank(self, allowed_sensitivity: Sequence[str] | None) -> int:
        if not allowed_sensitivity:
            return _SENSITIVITY_RANK["internal"]
        max_rank = _SENSITIVITY_RANK["public"]
        for level in allowed_sensitivity:
            max_rank = max(max_rank, _SENSITIVITY_RANK[self._normalize_sensitivity(level)])
        return max_rank


_DEFAULT_MEMORY_SERVICE = MemoryService()


def add_memory(
    content: str,
    type: str = "note",
    tags: Iterable[str] | None = None,
    source: str = "user",
    importance: int = 5,
    confidence: float = 0.8,
    sensitivity: str | None = None,
) -> str:
    return _DEFAULT_MEMORY_SERVICE.write(
        {
            "content": content,
            "type": type,
            "tags": list(tags) if tags is not None else None,
            "source": source,
            "importance": importance,
            "confidence": confidence,
            "sensitivity": sensitivity,
        }
    )


def search_memories(
    query: str,
    tags: Iterable[str] | None,
    limit: int = 10,
    allowed_sensitivity: Sequence[str] | None = None,
) -> list[dict[str, object]]:
    return _DEFAULT_MEMORY_SERVICE.retrieve(
        query,
        max_items=limit,
        tags=tags,
        allowed_sensitivity=allowed_sensitivity,
    )


def list_recent(limit: int = 20, allowed_sensitivity: Sequence[str] | None = None) -> list[dict[str, object]]:
    return _DEFAULT_MEMORY_SERVICE.list_recent(max_items=limit, allowed_sensitivity=allowed_sensitivity)


def get_memory_by_id(memory_id: str, allowed_sensitivity: Sequence[str] | None = None) -> dict[str, object] | None:
    return _DEFAULT_MEMORY_SERVICE.get_by_id(memory_id, allowed_sensitivity=allowed_sensitivity)


def delete_memory(memory_id: str) -> bool:
    return _DEFAULT_MEMORY_SERVICE.delete(memory_id)
