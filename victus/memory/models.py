from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass
class MemoryRecord:
    id: str
    ts: str
    scope: str
    kind: str
    text: str
    tags: List[str] = field(default_factory=list)
    source: str = "user"
    confidence: float = 0.7
    pii_risk: str = "low"
    ttl_days: Optional[int] = None

    @classmethod
    def create(
        cls,
        *,
        scope: str,
        kind: str,
        text: str,
        tags: Optional[List[str]] = None,
        source: str = "user",
        confidence: float = 0.7,
        pii_risk: str = "low",
        ttl_days: Optional[int] = None,
    ) -> "MemoryRecord":
        return cls(
            id=str(uuid4()),
            ts=datetime.utcnow().isoformat() + "Z",
            scope=scope,
            kind=kind,
            text=text,
            tags=tags or [],
            source=source,
            confidence=confidence,
            pii_risk=pii_risk,
            ttl_days=ttl_days,
        )

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "MemoryRecord":
        return cls(
            id=payload.get("id", str(uuid4())),
            ts=payload.get("ts", datetime.utcnow().isoformat() + "Z"),
            scope=payload.get("scope", "session"),
            kind=payload.get("kind", "context"),
            text=payload.get("text", ""),
            tags=list(payload.get("tags", []) or []),
            source=payload.get("source", "user"),
            confidence=float(payload.get("confidence", 0.7)),
            pii_risk=payload.get("pii_risk", "low"),
            ttl_days=payload.get("ttl_days"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "ts": self.ts,
            "scope": self.scope,
            "kind": self.kind,
            "text": self.text,
            "tags": self.tags,
            "source": self.source,
            "confidence": self.confidence,
            "pii_risk": self.pii_risk,
            "ttl_days": self.ttl_days,
        }
