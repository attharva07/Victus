from __future__ import annotations

import re
from typing import Optional

from core.logging.audit import AuditEvent, log_event
from core.orchestrator.policy import allow_intent
from core.orchestrator.schemas import Intent, IntentType

from adapters.llm.provider import LLMProvider


def classify_intent(text: str) -> Optional[Intent]:
    normalized = text.strip().lower()
    if not normalized:
        return None

    if re.search(r"\bhelp\b", normalized):
        return Intent(intent_type=IntentType.HELP, confidence=0.9, payload={})
    if re.search(r"\bstatus\b", normalized):
        return Intent(intent_type=IntentType.STATUS, confidence=0.8, payload={})

    return None


def orchestrate(text: str, actor: str, role: str) -> tuple[Optional[Intent], str]:
    intent = classify_intent(text)

    if intent is None:
        intent = LLMProvider().propose_intent(text)

    if intent is None:
        message = "I need more detail to determine an intent."
        log_event(
            AuditEvent(
                event_type="orchestrate",
                actor=actor,
                resource="/orchestrate",
                result="no_intent",
                metadata={"text": text[:100]},
            )
        )
        return None, message

    if not allow_intent(intent, role):
        message = "That request is not permitted under the current policy."
        log_event(
            AuditEvent(
                event_type="orchestrate",
                actor=actor,
                resource="/orchestrate",
                result="blocked",
                metadata={"intent": intent.intent_type},
            )
        )
        return intent, message

    message = "Intent recognized. No actions executed in Phase 1."
    log_event(
        AuditEvent(
            event_type="orchestrate",
            actor=actor,
            resource="/orchestrate",
            result="allowed",
            metadata={"intent": intent.intent_type},
        )
    )
    return intent, message
