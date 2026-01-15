from __future__ import annotations

from datetime import datetime
from typing import List

from .models import MemoryRecord
from .store import MemoryStore


class MemorySearch:
    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def search(self, query: str, top_k: int = 5) -> List[MemoryRecord]:
        normalized = query.lower().strip()
        if not normalized:
            return []
        terms = [term for term in normalized.split() if term]
        scored: List[tuple[float, MemoryRecord]] = []
        for record in self.store.all_records():
            score = self._score_record(record, terms)
            if score > 0:
                scored.append((score, record))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [record for _, record in scored[:top_k]]

    def recent(self, limit: int = 10) -> List[MemoryRecord]:
        return self.store.recent(limit)

    def _score_record(self, record: MemoryRecord, terms: List[str]) -> float:
        text = record.text.lower()
        match_score = sum(1 for term in terms if term in text)
        if match_score == 0:
            return 0.0
        recency_boost = self._recency_weight(record.ts)
        return match_score + recency_boost

    @staticmethod
    def _recency_weight(ts: str) -> float:
        try:
            parsed = datetime.fromisoformat(ts.replace("Z", ""))
        except ValueError:
            return 0.0
        days = (datetime.utcnow() - parsed).days
        if days <= 1:
            return 1.0
        if days <= 7:
            return 0.5
        if days <= 30:
            return 0.2
        return 0.0
