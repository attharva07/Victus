from __future__ import annotations

import pytest
from pydantic import ValidationError

from core.cognition.deliberator import Deliberator
from core.cognition.engine import CognitionEngine
from core.cognition.identity_controller import IdentityController
from core.cognition.models import IntentCandidate
from core.cognition.state import InMemorySessionStateStore
from core.orchestrator.policy import enforce_policy_gate


def test_interpreter_output_schema_validation_strict() -> None:
    with pytest.raises(ValidationError):
        IntentCandidate.model_validate({"action": "memory.add", "parameters": {}, "confidence": "0.8"})


def test_deliberator_confidence_thresholds() -> None:
    deliberator = Deliberator()
    low = deliberator.deliberate(IntentCandidate(action="memory.add", parameters={}, confidence=0.2), {}, {})
    mid = deliberator.deliberate(IntentCandidate(action="memory.add", parameters={}, confidence=0.6), {}, {})
    high = deliberator.deliberate(IntentCandidate(action="memory.add", parameters={}, confidence=0.9), {}, {})
    assert low.mode == "clarify"
    assert mid.mode == "suggest"
    assert high.mode == "act"


def test_identity_controller_memory_cap_and_sensitivity() -> None:
    identity = IdentityController()
    memories = [
        {"id": "1", "tags": ["general"]},
        {"id": "2", "tags": ["sensitive"], "sensitive": True},
        {"id": "3", "tags": ["general"]},
        {"id": "4", "tags": ["general"]},
    ]
    decision = Deliberator().deliberate(
        IntentCandidate(action="memory.delete", parameters={}, confidence=0.9, risk="high"), {}, {}
    )
    out = identity.resolve(user_text="please delete", decision=decision, session_state={}, memory_candidates=memories, memory_cap=2)
    assert out.persona_mode == "crisp_cautious"
    assert len(out.selected_memories) == 2
    assert all(not m.get("sensitive") for m in out.selected_memories)


def test_clarification_loop_prevention() -> None:
    engine = CognitionEngine(state_store=InMemorySessionStateStore())
    first = engine.run(session_id="s1", text="unclear", context={}, memory_candidates=[])
    second = engine.run(session_id="s1", text="still unclear", context={}, memory_candidates=[])
    assert first.decision.mode == "clarify"
    assert second.decision.mode in {"suggest", "clarify"}
    assert second.decision.mode == "suggest"


def test_high_risk_confirmation_required() -> None:
    denied = enforce_policy_gate(action="memory.delete", risk="high", confirmation_token=None)
    allowed = enforce_policy_gate(action="memory.delete", risk="high", confirmation_token="CONFIRM")
    assert denied.requires_confirmation is True
    assert denied.action_allowed is False
    assert allowed.action_allowed is True
