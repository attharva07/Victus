from __future__ import annotations

import re
from typing import Any, Protocol

from core.cognition.models import IntentCandidate


class Interpreter(Protocol):
    def interpret(self, text: str, context: dict[str, Any]) -> IntentCandidate: ...


class StubLLMInterpreter:
    """Stable adapter interface; currently deterministic heuristics for local use."""

    def interpret(self, text: str, context: dict[str, Any]) -> IntentCandidate:
        lowered = text.lower().strip()
        hinted_action = str(context.get("hinted_action", "")).strip()
        if hinted_action:
            return IntentCandidate(action=hinted_action, parameters=dict(context.get("hinted_parameters", {})), confidence=0.9)

        if "remember" in lowered:
            return IntentCandidate(action="memory.add", parameters={"content": text}, confidence=0.8)
        if re.search(r"\b(spent|paid|transaction)\b", lowered):
            return IntentCandidate(action="finance.add_transaction", parameters={}, confidence=0.55)
        if any(token in lowered for token in ("delete", "remove permanently")):
            return IntentCandidate(action="memory.delete", parameters={}, confidence=0.6, risk="high")
        return IntentCandidate(action="noop", parameters={}, confidence=0.3)
