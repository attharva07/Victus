from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel


class IntentType(str, Enum):
    HELP = "help"
    STATUS = "status"
    UNKNOWN = "unknown"


class Intent(BaseModel):
    intent_type: IntentType
    confidence: float
    payload: dict[str, Any] = {}


class OrchestrateRequest(BaseModel):
    text: str


class OrchestrateResponse(BaseModel):
    intent: Optional[Intent]
    actions_taken: list[dict[str, Any]]
    message: str
