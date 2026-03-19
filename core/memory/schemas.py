from __future__ import annotations

from pydantic import BaseModel, Field


VALID_TYPES = {"note", "fact", "task", "event", "preference", "observation"}
VALID_SENSITIVITIES = {"public", "internal", "sensitive", "critical"}


class MemoryWrite(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    type: str = Field(default="note")
    tags: list[str] = Field(default_factory=list)
    source: str = Field(default="user")
    importance: int = Field(default=5, ge=1, le=10)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    sensitivity: str = Field(default="internal")

    def model_post_init(self, __context: object) -> None:
        if self.type not in VALID_TYPES:
            raise ValueError(f"type must be one of {VALID_TYPES}")
        if self.sensitivity not in VALID_SENSITIVITIES:
            raise ValueError(f"sensitivity must be one of {VALID_SENSITIVITIES}")


class MemoryRecord(BaseModel):
    id: str
    ts: str
    type: str
    tags: list[str]
    source: str
    content: str
    importance: int
    confidence: float
    sensitivity: str


class MemoryCreateResponse(BaseModel):
    id: str
    message: str = "Memory stored."


class MemorySearchResponse(BaseModel):
    results: list[MemoryRecord]
    count: int


class MemoryListResponse(BaseModel):
    results: list[MemoryRecord]
    count: int


class MemoryDeleteResponse(BaseModel):
    deleted: bool
    id: str
