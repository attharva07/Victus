from __future__ import annotations

from typing import Any

from core.cognition.deliberator import Deliberator
from core.cognition.identity_controller import IdentityController
from core.cognition.interpreter import Interpreter, StubLLMInterpreter
from core.cognition.models import CognitionResult, IntentCandidate
from core.cognition.state import InMemorySessionStateStore


class CognitionEngine:
    def __init__(
        self,
        *,
        interpreter: Interpreter | None = None,
        deliberator: Deliberator | None = None,
        identity: IdentityController | None = None,
        state_store: InMemorySessionStateStore | None = None,
    ) -> None:
        self.interpreter = interpreter or StubLLMInterpreter()
        self.deliberator = deliberator or Deliberator()
        self.identity = identity or IdentityController()
        self.state_store = state_store or InMemorySessionStateStore()

    def run(
        self,
        *,
        session_id: str,
        text: str,
        context: dict[str, Any],
        memory_candidates: list[dict[str, Any]],
    ) -> CognitionResult:
        state = self.state_store.get(session_id)
        try:
            candidate = self.interpreter.interpret(text, context)
        except Exception:
            candidate = IntentCandidate(action="noop", parameters={}, confidence=0.0)

        decision = self.deliberator.deliberate(candidate, state.__dict__, context.get("cognition_config", {}))
        identity = self.identity.resolve(
            user_text=text,
            decision=decision,
            session_state=state.__dict__,
            memory_candidates=memory_candidates,
            memory_cap=int(context.get("memory_cap", 3)),
        )
        state_patch = dict(identity.state_patch)
        state_patch["last_intent"] = candidate.action
        if decision.mode == "act":
            state_patch["last_action"] = candidate.action
        new_state = self.state_store.patch(session_id, state_patch)

        return CognitionResult(intent=candidate, decision=decision, identity=identity, state=new_state.__dict__.copy())
