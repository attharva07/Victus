from __future__ import annotations

from pydantic import BaseModel, Field

from core.cognition.models import CandidateAction
from core.orchestrator.schemas import Intent

_ALLOWED_ACTIONS = {
    "noop",
    "chat.reply",
    "camera.status",
    "camera.capture",
    "camera.recognize",
    "memory.add",
    "memory.search",
    "memory.list",
    "memory.delete",
    "finance.add_transaction",
    "finance.list_transactions",
    "finance.summary",
    "files.list",
    "files.read",
    "files.write",
}


class CandidatePolicyDecision(BaseModel):
    action: str
    allowed: bool
    reason: str


class PolicyGateResult(BaseModel):
    decisions: list[CandidatePolicyDecision] = Field(default_factory=list)

    @property
    def allowed_actions(self) -> set[str]:
        return {item.action for item in self.decisions if item.allowed}

    @property
    def denied_reasons(self) -> dict[str, str]:
        return {item.action: item.reason for item in self.decisions if not item.allowed}


def validate_intent(intent: Intent) -> Intent:
    if intent.action not in _ALLOWED_ACTIONS:
        return Intent(action="noop", parameters={}, confidence=0.0)
    return intent


def evaluate_candidates(candidates: list[CandidateAction]) -> PolicyGateResult:
    decisions: list[CandidatePolicyDecision] = []
    for candidate in candidates:
        action = candidate.action
        lowered = action.lower()
        if action == "clarify":
            decisions.append(CandidatePolicyDecision(action=action, allowed=True, reason="safe_clarification"))
        elif lowered.startswith("admin."):
            decisions.append(CandidatePolicyDecision(action=action, allowed=False, reason="admin_actions_require_manual_review"))
        elif lowered in _ALLOWED_ACTIONS:
            decisions.append(CandidatePolicyDecision(action=action, allowed=True, reason="allowlisted"))
        else:
            decisions.append(CandidatePolicyDecision(action=action, allowed=False, reason="not_allowlisted"))
    return PolicyGateResult(decisions=decisions)
