from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ActionIntent(BaseModel):
    action: str = Field(min_length=3)
    parameters: dict[str, Any] = Field(default_factory=dict)
    context: dict[str, Any] = Field(default_factory=dict)


class RequestEnvelope(BaseModel):
    request_id: str = Field(min_length=3)
    correlation_id: str | None = None
    intent: ActionIntent
    metadata: dict[str, Any] = Field(default_factory=dict)


class PolicyDecision(BaseModel):
    allowed: bool
    reason: str
    action: str


class ExecutionError(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class UIHints(BaseModel):
    card_type: str | None = None
    priority: Literal["low", "normal", "high"] | None = None
    expandable: bool | None = None


class ToneHints(BaseModel):
    mode: str | None = None


class ExecutionResult(BaseModel):
    request_id: str
    correlation_id: str | None = None
    executed: bool
    status: Literal["success", "error"]
    actions: list[dict[str, Any]] = Field(default_factory=list)
    message: str | None = None
    ui_hints: UIHints | None = None
    tone_hints: ToneHints | None = None
    error: ExecutionError | None = None


class AuditEvent(BaseModel):
    request_id: str
    correlation_id: str | None = None
    action: str
    sanitized_parameters: dict[str, Any]
    status: Literal["started", "success", "error"]
    started_at: datetime
    ended_at: datetime | None = None
    error_summary: str | None = None


class CognitionAction(BaseModel):
    action: str
    parameters: dict[str, Any] = Field(default_factory=dict)


class FutureCognitionOutput(BaseModel):
    goal: str
    actions: list[CognitionAction]
    ui_mode: str | None = None
    tone_mode: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    needs_clarification: bool = False
    clarification_question: str | None = None
