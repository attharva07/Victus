from __future__ import annotations

import pytest

from victus.contracts.orchestrator_result import OrchestratorResult
from victus.contracts.rendered_result import RenderedResult


def test_orchestrator_result_schema_and_round_trip() -> None:
    payload = {
        "trace_id": "t1",
        "decision": "allow",
        "intent": {"action": "memory.add", "parameters": {"content": "x"}},
        "confidence": 0.9,
        "confidence_tier": "high",
        "policy": {"allowed": True, "reason_code": "allowed"},
        "required_inputs": [],
        "ui_hints": {"primary_cards": ["memory"], "locks": [], "safe_fields": [], "redactions": []},
        "tool_results": [],
    }
    model = OrchestratorResult.from_dict(payload)
    assert model.to_dict() == payload
    assert OrchestratorResult.from_json(model.to_json()).to_dict() == payload


def test_rendered_result_json_round_trip() -> None:
    rendered = RenderedResult(
        trace_id="t2",
        headline="ok",
        body="body",
        bullets=["a"],
        tone_profile="neutral",
        verbosity_level="normal",
        ui_copy_hints={"x": "y"},
    )
    assert RenderedResult.from_json(rendered.to_json()).model_dump() == rendered.model_dump()


def test_invalid_decision_policy_consistency_raises() -> None:
    with pytest.raises(Exception):
        OrchestratorResult(
            trace_id="bad",
            decision="deny",
            intent={"action": "blocked", "parameters": {}},
            confidence=0.9,
            confidence_tier="high",
            policy={"allowed": True, "reason_code": "allowed"},
            required_inputs=[],
            ui_hints={"primary_cards": [], "locks": [], "safe_fields": [], "redactions": []},
            tool_results=[],
        )
