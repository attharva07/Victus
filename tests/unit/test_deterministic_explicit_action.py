from __future__ import annotations

from core.orchestrator.deterministic import parse_intent


def test_explicit_memory_add_payload_parses_to_action_and_parameters() -> None:
    intent = parse_intent("memory.add: I like dark mode")

    assert intent is not None
    assert intent.action == "memory.add"
    assert intent.parameters.get("content") == "I like dark mode"


def test_explicit_memory_add_missing_payload_returns_specific_clarify() -> None:
    intent = parse_intent("memory.add:")

    assert intent is not None
    assert intent.action == "noop"
    assert intent.parameters.get("error") == "clarify"
    message = str(intent.parameters.get("message", ""))
    assert "content" in message
    assert "memory.add" in message
    assert "memory, finance, files, or camera" not in message


def test_unknown_explicit_action_returns_unsupported_error() -> None:
    intent = parse_intent("unknown.tool: hi")

    assert intent is not None
    assert intent.action == "noop"
    assert intent.parameters.get("error") == "unknown_intent"
    assert "Unsupported explicit action" in str(intent.parameters.get("message", ""))


def test_explicit_finance_add_transaction_payload_parses_to_structured_parameters() -> None:
    intent = parse_intent("finance.add_transaction: $6 Starbucks")

    assert intent is not None
    assert intent.action == "finance.add_transaction"
    assert intent.parameters.get("amount") == 6.0
    assert intent.parameters.get("merchant") == "Starbucks"
    assert intent.parameters.get("category") == "Starbucks"
    assert intent.parameters.get("currency") == "USD"
    assert intent.parameters.get("occurred_at")
