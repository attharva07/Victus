from pathlib import Path
from typing import Dict, List, Optional

from ..util.jsonl import append_jsonl, read_jsonl
from .models import MemoryRecord

MEMORY_PATH = Path("data/memory/memory.jsonl")


class MemoryStoreError(PermissionError):
    pass


def append_memory(record: Dict, *, authorized: bool = False) -> None:
    if not authorized:
        raise MemoryStoreError("Memory writes must go through the service approval flow")
    append_jsonl(MEMORY_PATH, record)


def list_memory(limit: Optional[int] = None, category: Optional[str] = None) -> List[MemoryRecord]:
    records = [MemoryRecord(**rec) for rec in read_jsonl(MEMORY_PATH)]
    if category:
        records = [r for r in records if r.category == category]
    if limit:
        records = records[-limit:]
    return records


def get_memory_by_id(memory_id: str) -> Optional[MemoryRecord]:
    for record in list_memory():
        if record.id == memory_id:
            return record
    return None
