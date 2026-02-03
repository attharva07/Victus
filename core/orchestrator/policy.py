from __future__ import annotations

from core.orchestrator.schemas import Intent, IntentType


def allow_intent(intent: Intent, role: str) -> bool:
    """Policy gate for intents.

    Phase 1 only allows read-only intents.
    """
    if intent.intent_type in {IntentType.HELP, IntentType.STATUS}:
        return True
    if intent.intent_type == IntentType.UNKNOWN:
        return False
    return role == "admin"
