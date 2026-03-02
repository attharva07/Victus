from __future__ import annotations

from victus.engines import LogicEngine


def test_logic_engine_realistic_prompts() -> None:
    engine = LogicEngine()
    prompts = [
        ("remind me to call mom at 6pm", "allow", "productivity.reminder.create", [], True, "high"),
        ("remind me to call mom", "needs_clarification", "productivity.reminder.create", ["time"], True, "medium"),
        ("what is the system status", "allow", "system.status.query", [], True, "high"),
        ("can you do the thing", "needs_clarification", "unknown", ["action"], True, "low"),
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


def test_logic_engine_deterministic_except_trace_id() -> None:
    engine = LogicEngine()
    one = engine.run("remind me to call mom", context={}).to_dict()
    two = engine.run("remind me to call mom", context={}).to_dict()
    one.pop("trace_id")
    two.pop("trace_id")
    assert one == two
