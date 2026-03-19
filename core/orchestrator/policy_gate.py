from __future__ import annotations

from core.config import get_security_config
from core.orchestrator.contracts import ActionIntent, PolicyDecision


def evaluate_action(intent: ActionIntent) -> PolicyDecision:
    enabled = set(get_security_config().enabled_tools)
    if intent.action not in enabled:
        return PolicyDecision(allowed=False, reason="action_not_enabled", action=intent.action)
    return PolicyDecision(allowed=True, reason="allowlisted", action=intent.action)
