from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class CandidateAction(BaseModel):
    action: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    score_total: float = Field(ge=0.0, le=1.0)
    score_breakdown: dict[str, float] = Field(default_factory=dict)
    rationale: str = Field(max_length=280)
    required_permissions: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class DecisionPlan(BaseModel):
    candidates: list[CandidateAction] = Field(default_factory=list)
    selected: CandidateAction | None = None
    notes: list[str] = Field(default_factory=list)
    trace_id: str


class IntentCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    action: str
    parameters: dict[str, Any]
    confidence: float = Field(ge=0.0, le=1.0)
    requested_memory_ops: dict[str, Any] | None = None
    risk: Literal["low", "medium", "high", "blocked"] | None = None


class Decision(BaseModel):
    mode: Literal["act", "clarify", "refuse", "suggest"]
    risk: Literal["low", "medium", "high", "blocked"]
    action_allowed: bool
    clarification_question: str | None = None
    requires_confirmation: bool = False


class IdentityResult(BaseModel):
    persona_mode: str
    selected_memories: list[dict[str, Any]] = Field(default_factory=list)
    state_patch: dict[str, Any] = Field(default_factory=dict)


class CognitionResult(BaseModel):
    intent: IntentCandidate
    decision: Decision
    identity: IdentityResult
    state: dict[str, Any]
