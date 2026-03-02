from __future__ import annotations

import json
from pathlib import Path

from victus.contracts.orchestrator_result import OrchestratorResult
from victus.engines import PersonalityEngine


SNAPSHOT_PATH = Path("tests/fixtures/snapshots/personality_engine_golden.json")


def _fixtures() -> list[OrchestratorResult]:
    return [
        OrchestratorResult(
            trace_id="trace-a",
            decision="allow",
            intent={"action": "memory.add", "parameters": {"content": "x"}},
            confidence=0.95,
            confidence_tier="high",
            policy={"allowed": True, "reason_code": "allowed"},
            required_inputs=[],
            ui_hints={"primary_cards": ["memory"], "locks": [], "safe_fields": [], "redactions": []},
            tool_results=[],
        ),
        OrchestratorResult(
            trace_id="trace-b",
            decision="allow",
            intent={"action": "productivity.reminder.create", "parameters": {"task": "call", "time": "6pm"}},
            confidence=0.86,
            confidence_tier="high",
            policy={"allowed": True, "reason_code": "allowed"},
            required_inputs=[],
            ui_hints={"primary_cards": ["reminders"], "locks": [], "safe_fields": [], "redactions": []},
            tool_results=[],
        ),
        OrchestratorResult(
            trace_id="trace-c",
            decision="needs_clarification",
            intent={"action": "productivity.reminder.create", "parameters": {"task": "call"}},
            confidence=0.65,
            confidence_tier="medium",
            policy={"allowed": True, "reason_code": "allowed"},
            required_inputs=["time"],
            ui_hints={"primary_cards": ["reminders"], "locks": [], "safe_fields": [], "redactions": []},
            tool_results=[],
        ),
        OrchestratorResult(
            trace_id="trace-d",
            decision="deny",
            intent={"action": "blocked", "parameters": {"text": "delete system32"}},
            confidence=0.95,
            confidence_tier="high",
            policy={"allowed": False, "reason_code": "unsafe_action"},
            required_inputs=[],
            ui_hints={"primary_cards": ["general"], "locks": ["policy"], "safe_fields": [], "redactions": ["sensitive_terms"]},
            tool_results=[],
        ),
        OrchestratorResult(
            trace_id="trace-e",
            decision="allow",
            intent={"action": "system.status.query", "parameters": {}},
            confidence=0.8,
            confidence_tier="high",
            policy={"allowed": True, "reason_code": "allowed"},
            required_inputs=[],
            ui_hints={"primary_cards": ["system"], "locks": [], "safe_fields": [], "redactions": []},
            tool_results=[],
        ),
        OrchestratorResult(
            trace_id="trace-f",
            decision="needs_clarification",
            intent={"action": "unknown", "parameters": {}},
            confidence=0.4,
            confidence_tier="low",
            policy={"allowed": True, "reason_code": "allowed"},
            required_inputs=["action"],
            ui_hints={"primary_cards": ["general"], "locks": [], "safe_fields": [], "redactions": []},
            tool_results=[],
        ),
    ]


def test_personality_snapshots() -> None:
    engine = PersonalityEngine()
    fixtures = _fixtures()
    profiles = [{"tone": "friendly", "verbosity": "short"}, {"tone": "formal", "verbosity": "detailed"}]

    produced: list[dict[str, object]] = []
    for item in fixtures:
        for profile in profiles:
            rendered = engine.render(item, profile)
            dumped = rendered.model_dump()
            dumped.pop("trace_id", None)
            produced.append({"input_action": item.intent["action"], "profile": profile, "output": dumped})

    expected = json.loads(SNAPSHOT_PATH.read_text())
    assert produced == expected
