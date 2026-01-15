from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List

from .models import MemoryRecord


class MemoryStore:
    def __init__(self, base_path: Path | None = None) -> None:
        self.base_path = base_path or Path("victus_data") / "memory"
        self.project_path = self.base_path / "project.jsonl"
        self.user_path = self.base_path / "user.jsonl"
        self.session_records: List[MemoryRecord] = []
        self._ensure_paths()

    def _ensure_paths(self) -> None:
        self.base_path.mkdir(parents=True, exist_ok=True)
        for path in [self.project_path, self.user_path]:
            if not path.exists():
                path.write_text("")

    def append(self, record: MemoryRecord) -> None:
        if record.scope == "session":
            self.session_records.append(record)
            return
        path = self.project_path if record.scope == "project" else self.user_path
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")

    def load_scope(self, scope: str) -> List[MemoryRecord]:
        if scope == "session":
            return list(self.session_records)
        path = self.project_path if scope == "project" else self.user_path
        if not path.exists():
            return []
        records: List[MemoryRecord] = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                records.append(MemoryRecord.from_dict(payload))
        return records

    def all_records(self) -> List[MemoryRecord]:
        records: List[MemoryRecord] = []
        records.extend(self.load_scope("session"))
        records.extend(self.load_scope("project"))
        records.extend(self.load_scope("user"))
        return records

    def recent(self, limit: int = 10) -> List[MemoryRecord]:
        records = self.all_records()
        records.sort(key=lambda record: record.ts, reverse=True)
        return records[:limit]

    def append_many(self, records: Iterable[MemoryRecord]) -> None:
        for record in records:
            self.append(record)
