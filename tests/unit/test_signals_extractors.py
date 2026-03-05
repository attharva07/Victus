from __future__ import annotations

from core.signals.extractors import extract_signals


def test_extract_signals_finance_spent_at_merchant() -> None:
    signals = extract_signals("I spent $6 at Starbucks")

    assert signals.amount == 6.0
    assert signals.merchant is not None
    assert "Starbucks" in signals.merchant
    assert signals.intent_hint == "finance.add_transaction"


def test_extract_signals_add_transaction_without_currency_symbol() -> None:
    signals = extract_signals("add transaction 6 Starbucks")

    assert signals.intent_hint == "finance.add_transaction"
    assert signals.amount == 6.0
    assert signals.merchant == "Starbucks"


def test_extract_signals_memory_content() -> None:
    signals = extract_signals("remember that I like dark mode")

    assert signals.intent_hint == "memory.add"
    content = signals.evidence.get("memory_content")
    assert isinstance(content, str)
    assert "I like dark mode" in content
