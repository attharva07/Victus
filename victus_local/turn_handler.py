from __future__ import annotations

from typing import AsyncIterator, List

from victus.app import VictusApp
from victus.core.schemas import TurnEvent
from victus.memory.gate import MemoryGate
from victus.memory.models import MemoryRecord
from victus.memory.search import MemorySearch
from victus.memory.store import MemoryStore


class TurnHandler:
    def __init__(self, app: VictusApp, store: MemoryStore | None = None) -> None:
        self.app = app
        self.store = store or MemoryStore()
        self.search = MemorySearch(self.store)
        self.gate = MemoryGate()

    async def run_turn(self, message: str) -> AsyncIterator[TurnEvent]:
        memory_hits = self.search.search(message, top_k=3)
        if memory_hits:
            yield TurnEvent(
                event="memory_used",
                result={
                    "count": len(memory_hits),
                    "ids": [record.id for record in memory_hits],
                    "items": [self._to_summary(record) for record in memory_hits],
                },
            )

        memory_prompt = self._format_memory_prompt(memory_hits)
        async for event in self.app.run_request(message, memory_prompt=memory_prompt):
            yield event

        record = self._maybe_write_memory(message)
        if record:
            yield TurnEvent(
                event="memory_written",
                result=self._to_summary(record),
            )

    def _maybe_write_memory(self, message: str) -> MemoryRecord | None:
        candidate = self.gate.extract_candidate(message, source="user")
        if not candidate:
            return None
        record = self.gate.build_record(candidate)
        self.store.append(record)
        return record

    @staticmethod
    def _format_memory_prompt(records: List[MemoryRecord]) -> str:
        if not records:
            return ""
        lines = ["Relevant memory:"]
        for record in records:
            lines.append(f"- ({record.kind}) {record.text}")
        return "\n".join(lines)

    @staticmethod
    def _to_summary(record: MemoryRecord) -> dict:
        return {
            "id": record.id,
            "ts": record.ts,
            "scope": record.scope,
            "kind": record.kind,
            "text": record.text,
            "tags": record.tags,
            "source": record.source,
            "confidence": record.confidence,
            "pii_risk": record.pii_risk,
        }
