from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Memory:
    id: str
    ts: str
    type: str
    tags: list[str]
    source: str
    content: str
    importance: int
    confidence: float
    sensitivity: str
