from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SignalBundle(BaseModel):
    raw_text: str
    amount: float | None = None
    currency: str | None = None
    merchant: str | None = None
    category_hint: str | None = None
    datetime_hint: str | None = None
    intent_hint: str | None = None
    confidence: float = 0.0
    evidence: dict[str, Any] = Field(default_factory=dict)
