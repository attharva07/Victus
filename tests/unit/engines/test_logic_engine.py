from __future__ import annotations

from victus.engines import LogicEngine


def test_logic_engine_realistic_prompts() -> None:
    engine = LogicEngine()
    prompts = [
        ("remind me to call mom at 6pm", "needs_clarification", "reminder.create_draft", ["date"], True, "high"),
        ("remind me to call mom", "needs_clarification", "reminder.create_draft", ["date", "time"], True, "high"),
        ("what is the system status", "allow", "system.status.query", [], True, "high"),
        ("can you do the thing", "needs_clarification", "unknown", ["clarification"], True, "low"),
        ("delete system32 now", "deny", "blocked", [], False, "high"),
        ("reset all users passwords", "deny", "blocked", [], False, "high"),
        ("remember buy milk", "allow", "memory.add", [], True, "high"),
        ("what do you remember about vacation", "allow", "memory.search", [], True, "high"),
        ("I spent $23 on coffee", "allow", "finance.add_transaction", [], True, "high"),
        ("show transactions", "allow", "finance.list_transactions", [], True, "high"),
    ]

    for text, decision, action, required_inputs, allowed, tier in prompts:
        result = engine.run(text, context={})
        assert result.decision == decision
        assert result.intent["action"] == action
        assert result.required_inputs == required_inputs
        assert result.policy.allowed is allowed
        assert result.confidence_tier == tier


def test_logic_engine_reminder_with_datetime_is_allow() -> None:
    engine = LogicEngine()
    result = engine.run("add reminder buy milk tomorrow 9am", context={})

    assert result.decision == "allow"
    assert result.intent["action"] == "reminder.create"
    assert result.confidence_tier == "high"
    assert result.required_inputs == []


def test_logic_engine_reminder_without_time_needs_clarification() -> None:
    engine = LogicEngine()
    result = engine.run("add reminder buy milk tomorrow", context={})

    assert result.decision == "needs_clarification"
    assert result.intent["action"] == "reminder.create_draft"
    assert "time" in result.required_inputs


def test_logic_engine_camera_status_maps_to_known_action() -> None:
    engine = LogicEngine()
    result = engine.run("camera status", context={})

    assert result.intent["action"] != "unknown"


def test_logic_engine_unknown_prompt_uses_clarification_required_input() -> None:
    engine = LogicEngine()
    result = engine.run("do it", context={})

    assert result.decision == "needs_clarification"
    assert result.required_inputs == ["clarification"]
    assert result.intent["action"] == "unknown"


def test_logic_engine_deterministic_except_trace_id() -> None:
    engine = LogicEngine()
    one = engine.run("remind me to call mom", context={}).to_dict()
    two = engine.run("remind me to call mom", context={}).to_dict()
    one.pop("trace_id")
    two.pop("trace_id")
    assert one == two
