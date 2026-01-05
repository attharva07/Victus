"""Persistent memory store with gated writes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_STORE_PATH = Path("victus/data/memory/store.json")
MEMORY_PATH = DEFAULT_STORE_PATH


class MemoryStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text(json.dumps({"items": []}, indent=2), encoding="utf-8")

    def _load(self) -> Dict[str, List[dict]]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def add(self, item: Dict[str, object]) -> None:
        data = self._load()
        data.setdefault("items", []).append(item)
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def list(self, domain: Optional[str] = None) -> List[dict]:
        data = self._load()
        items = data.get("items", [])
        if domain:
            items = [item for item in items if item.get("domain") == domain]
        return items


class MemoryStoreError(PermissionError):
    pass


def append_memory(record: Dict, *, authorized: bool = False) -> None:
    if not authorized:
        raise MemoryStoreError("Memory writes must go through manual review")
    store = MemoryStore(DEFAULT_STORE_PATH)
    store.add(record)


def list_memory(limit: Optional[int] = None, domain: Optional[str] = None) -> List[dict]:
    store = MemoryStore(DEFAULT_STORE_PATH)
    records = store.list(domain=domain)
    if limit:
        records = records[-limit:]
    return records


def get_memory_by_id(memory_id: str) -> Optional[dict]:
    for item in list_memory():
        if item.get("id") == memory_id:
            return item
    return None
