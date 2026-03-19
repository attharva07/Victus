from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


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
