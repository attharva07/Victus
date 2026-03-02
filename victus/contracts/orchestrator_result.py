from __future__ import annotations

from typing import Any, Dict, List, Literal

from pydantic import BaseModel, Field, model_validator


Decision = Literal["allow", "deny", "needs_clarification"]
ConfidenceTier = Literal["low", "medium", "high"]


class PolicyResult(BaseModel):
    allowed: bool
    reason_code: str


class UIHints(BaseModel):
    primary_cards: List[str] = Field(default_factory=list)
    locks: List[str] = Field(default_factory=list)
    safe_fields: List[str] = Field(default_factory=list)
    redactions: List[str] = Field(default_factory=list)


class OrchestratorResult(BaseModel):
    trace_id: str
    decision: Decision
    intent: Dict[str, Any]
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_tier: ConfidenceTier
    policy: PolicyResult
    required_inputs: List[str] = Field(default_factory=list)
    ui_hints: UIHints
    tool_results: List[Dict[str, Any]] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_contract(self) -> "OrchestratorResult":
        if "action" not in self.intent or "parameters" not in self.intent:
            raise ValueError("intent must include action and parameters")
        if self.decision == "allow" and not self.policy.allowed:
            raise ValueError("allow decisions require policy.allowed=True")
        if self.decision == "deny" and self.policy.allowed:
            raise ValueError("deny decisions require policy.allowed=False")
        if self.decision == "needs_clarification" and not self.policy.allowed:
            raise ValueError("needs_clarification must not be policy denied")
        return self

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "OrchestratorResult":
        return cls.model_validate(payload)

    def to_json(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_json(cls, raw: str) -> "OrchestratorResult":
        return cls.model_validate_json(raw)
