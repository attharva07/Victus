from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel


VerbosityLevel = Literal["short", "normal", "detailed"]


class RenderedResult(BaseModel):
    trace_id: str
    headline: str
    body: str
    bullets: List[str]
    tone_profile: str
    verbosity_level: VerbosityLevel
    ui_copy_hints: Optional[Dict[str, Any]] = None

    def to_json(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_json(cls, raw: str) -> "RenderedResult":
        return cls.model_validate_json(raw)
