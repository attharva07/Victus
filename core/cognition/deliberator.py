from __future__ import annotations

from typing import Any

from core.cognition.models import Decision, IntentCandidate


class Deliberator:
    def deliberate(self, candidate: IntentCandidate, session_state: dict[str, Any], config: dict[str, Any]) -> Decision:
        low = float(config.get("confidence_low", 0.4))
        high = float(config.get("confidence_high", 0.75))
        blocked_actions = set(config.get("blocked_actions", []))
        if candidate.action in blocked_actions:
            return Decision(mode="refuse", risk="blocked", action_allowed=False, clarification_question="That action is blocked by policy.")

        risk = candidate.risk or ("high" if "delete" in candidate.action else "low")

        if session_state.get("pending_clarification") and candidate.confidence < high:
            return Decision(mode="suggest", risk=risk, action_allowed=False, clarification_question="I can suggest the next step once you clarify.")

        if candidate.action == "noop":
            return Decision(mode="clarify", risk="low", action_allowed=False, clarification_question="What tool should I use?")
        if candidate.confidence < low:
            return Decision(mode="clarify", risk=risk, action_allowed=False, clarification_question="Could you clarify your intent?")
        if candidate.confidence < high:
            return Decision(mode="suggest", risk=risk, action_allowed=False, clarification_question="I can do this once you confirm details.")
        return Decision(mode="act", risk=risk, action_allowed=True, requires_confirmation=risk == "high")
