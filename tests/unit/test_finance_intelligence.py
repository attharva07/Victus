from __future__ import annotations

from datetime import datetime, timezone

from core.finance.intelligence import FinanceCognition, FinanceRuleEngine
from core.finance.service import generate_finance_brief


def test_rule_engine_credit_and_budget_alerts() -> None:
    engine = FinanceRuleEngine()
    snapshot = {
        "cards": [
            {
                "id": "card-1",
                "name": "Rewards Card",
                "credit_limit_cents": 100_000,
                "current_balance_cents": 85_000,
                "due_in_days": 1,
                "statement_in_days": 2,
                "autopay_enabled": False,
            }
        ],
        "budget": {"id": "b1", "total_limit_cents": 120_000, "categories": {"dining": 20_000}},
        "transactions": [
            {"amount_cents": -18_000, "category": "dining"},
            {"amount_cents": -10_000, "category": "dining"},
        ],
    }
    alerts = engine.evaluate(snapshot, now=datetime(2026, 1, 20, tzinfo=timezone.utc))
    reasons = {item["reason"] for item in alerts}
    assert "credit_utilization_high" in reasons
    assert "card_due_date" in reasons
    assert "statement_close_warning" in reasons
    assert "category_overspend" in reasons


def test_recurring_detection_and_behavior_pattern() -> None:
    cognition = FinanceCognition()
    tx = [
        {"amount_cents": -1000, "merchant": "StreamFlix", "ts": "2026-01-01T00:00:00+00:00"},
        {"amount_cents": -1100, "merchant": "StreamFlix", "ts": "2026-02-01T00:00:00+00:00"},
        {"amount_cents": -1200, "merchant": "StreamFlix", "ts": "2026-03-01T00:00:00+00:00"},
        {"amount_cents": -9000, "merchant": "Mall", "ts": "2026-03-15T00:00:00+00:00"},
    ]
    recurring = cognition.detect_recurring_expenses(tx)
    assert recurring[0]["merchant"] == "streamflix"

    insights = cognition.analyze(tx, paycheck_days=[15])
    patterns = {item["pattern"] for item in insights}
    assert "spending_drift" in patterns
    assert "post_payday_spike" in patterns


def test_generate_finance_brief_contains_reports() -> None:
    snapshot = {
        "transactions": [
            {"amount_cents": -2500, "category": "coffee", "merchant": "Cafe", "ts": "2026-01-15T00:00:00+00:00"},
            {"amount_cents": 100000, "category": "income", "merchant": "Employer", "ts": "2026-01-10T00:00:00+00:00"},
        ],
        "summary": {"totals": {"coffee": -2500}},
        "cards": [],
        "budget": {"total_limit_cents": 50000, "categories": {"coffee": 5000}},
        "savings_goals": [],
        "holdings": [],
        "watchlist": [],
        "paycheck_days": [10],
    }
    brief = generate_finance_brief(snapshot)
    assert "daily_brief" in brief
    assert "weekly_summary" in brief
    assert isinstance(brief["recommendations"], list)
