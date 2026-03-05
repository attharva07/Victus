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


class DecisionPolicyResult(BaseModel):
    action_allowed: bool
    requires_confirmation: bool = False
    blocked_reason: str | None = None


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


def enforce_policy_gate(
    *,
    action: str,
    risk: str,
    confirmation_token: str | None = None,
    allowlist: set[str] | None = None,
    blocked_actions: set[str] | None = None,
) -> DecisionPolicyResult:
    effective_allowlist = allowlist or _ALLOWED_ACTIONS
    blocked = blocked_actions or set()
    if action in blocked:
        return DecisionPolicyResult(action_allowed=False, blocked_reason="blocked_action")
    if action not in effective_allowlist:
        return DecisionPolicyResult(action_allowed=False, blocked_reason="not_allowlisted")
    if risk == "blocked":
        return DecisionPolicyResult(action_allowed=False, blocked_reason="blocked_risk")
    if risk == "high" and confirmation_token != "CONFIRM":
        return DecisionPolicyResult(action_allowed=False, requires_confirmation=True, blocked_reason="confirmation_required")
    return DecisionPolicyResult(action_allowed=True)
