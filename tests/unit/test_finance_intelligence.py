from __future__ import annotations

from datetime import datetime, timezone

from core.finance.intelligence import (
    FinanceAlertEngine,
    FinanceCognition,
    FinanceGuidanceEngine,
    FinanceInsightEngine,
)


# ===========================================================================
# E. Alert Engine Tests
# ===========================================================================

def test_alert_engine_credit_alerts() -> None:
    engine = FinanceAlertEngine()
    snapshot = {
        "cards": [
            {
                "id": "card-1",
                "name": "Rewards Card",
                "credit_limit_cents": 100_000,
                "current_balance_cents": 85_000,
            }
        ],
        "transactions": [],
    }
    alerts = engine.evaluate(snapshot, now=datetime(2026, 1, 20, tzinfo=timezone.utc))
    types = {a["type"] for a in alerts}
    assert "credit_utilization_high" in types


def test_alert_engine_budget_alerts() -> None:
    engine = FinanceAlertEngine()
    snapshot = {
        "budgets": [
            {"id": "b1", "name": "Dining", "category_id": "dining", "amount_limit_cents": 20_000},
        ],
        "transactions": [
            {"amount_cents": -18_000, "category_id": "dining", "direction": "expense"},
            {"amount_cents": -5_000, "category_id": "dining", "direction": "expense"},
        ],
    }
    alerts = engine.evaluate(snapshot, now=datetime(2026, 1, 20, tzinfo=timezone.utc))
    types = {a["type"] for a in alerts}
    assert "budget_exceeded" in types


def test_alert_engine_bill_alerts() -> None:
    engine = FinanceAlertEngine()
    snapshot = {
        "bills": [
            {"id": "bill-1", "name": "Rent", "due_date": "2026-01-18", "status": "pending"},
        ],
        "transactions": [],
    }
    alerts = engine.evaluate(snapshot, now=datetime(2026, 1, 20, tzinfo=timezone.utc))
    types = {a["type"] for a in alerts}
    assert "bill_overdue" in types


def test_alert_engine_savings_alerts() -> None:
    engine = FinanceAlertEngine()
    snapshot = {
        "savings_goals": [
            {
                "id": "g1", "name": "Vacation", "status": "active",
                "target_amount_cents": 500_000, "current_progress_cents": 50_000,
                "target_date": "2026-01-25",
            },
        ],
        "transactions": [],
    }
    alerts = engine.evaluate(snapshot, now=datetime(2026, 1, 20, tzinfo=timezone.utc))
    types = {a["type"] for a in alerts}
    assert "savings_behind_pace" in types


# ===========================================================================
# F. Insight Engine Tests
# ===========================================================================

def test_insight_engine_category_breakdown() -> None:
    engine = FinanceInsightEngine()
    transactions = [
        {"amount_cents": -5000, "direction": "expense", "category_id": "dining", "merchant": "Cafe", "transaction_date": "2026-03-10"},
        {"amount_cents": -3000, "direction": "expense", "category_id": "coffee", "merchant": "Coffee Shop", "transaction_date": "2026-03-11"},
        {"amount_cents": -2000, "direction": "expense", "category_id": "grocery", "merchant": "Market", "transaction_date": "2026-03-12"},
    ]
    insights = engine.analyze(transactions)
    patterns = {i["pattern"] for i in insights}
    assert "category_breakdown" in patterns


def test_insight_engine_recurring_detection() -> None:
    engine = FinanceInsightEngine()
    transactions = [
        {"amount_cents": -1000, "direction": "expense", "merchant": "StreamFlix", "transaction_date": f"2026-0{m}-01"}
        for m in range(1, 4)
    ]
    insights = engine.analyze(transactions)
    patterns = {i["pattern"] for i in insights}
    assert "recurring_expense_detection" in patterns


def test_insight_engine_month_over_month() -> None:
    engine = FinanceInsightEngine()
    transactions = [
        {"amount_cents": -5000, "direction": "expense", "merchant": "Store", "transaction_date": "2026-01-15"},
        {"amount_cents": -10000, "direction": "expense", "merchant": "Store", "transaction_date": "2026-02-15"},
    ]
    insights = engine.analyze(transactions)
    patterns = {i["pattern"] for i in insights}
    assert "month_over_month_comparison" in patterns


def test_insight_engine_spending_leaks() -> None:
    engine = FinanceInsightEngine()
    transactions = [
        {"amount_cents": -500, "direction": "expense", "merchant": "Snack Shop", "transaction_date": f"2026-03-{d:02d}"}
        for d in range(1, 6)
    ]
    insights = engine.analyze(transactions)
    patterns = {i["pattern"] for i in insights}
    assert "spending_leaks" in patterns


# ===========================================================================
# G. Guidance Engine Tests
# ===========================================================================

def test_guidance_engine_overspending() -> None:
    engine = FinanceGuidanceEngine()
    guidance = engine.generate(
        transactions=[
            {"amount_cents": -30000, "direction": "expense", "category_id": "dining"},
        ],
        budgets=[
            {"id": "b1", "name": "Dining", "category_id": "dining", "amount_limit_cents": 20000},
        ],
    )
    assert any("Reduce spending" in g["title"] for g in guidance)


def test_guidance_engine_savings() -> None:
    engine = FinanceGuidanceEngine()
    guidance = engine.generate(
        transactions=[],
        savings_goals=[
            {"id": "g1", "name": "Vacation", "status": "active",
             "target_amount_cents": 500000, "current_progress_cents": 10000},
        ],
    )
    assert any("Accelerate savings" in g["title"] for g in guidance)


def test_guidance_engine_bills() -> None:
    engine = FinanceGuidanceEngine()
    guidance = engine.generate(
        transactions=[],
        bills=[
            {"id": "bill-1", "name": "Rent", "amount_expected_cents": 150000,
             "status": "pending", "due_date": "2026-04-01"},
        ],
    )
    assert any("Upcoming bill" in g["title"] for g in guidance)


def test_guidance_engine_subscriptions() -> None:
    engine = FinanceGuidanceEngine()
    guidance = engine.generate(
        transactions=[
            {"amount_cents": -1000, "direction": "expense", "merchant": "StreamFlix"},
            {"amount_cents": -1000, "direction": "expense", "merchant": "StreamFlix"},
            {"amount_cents": -1000, "direction": "expense", "merchant": "StreamFlix"},
        ],
    )
    assert any("subscription" in g["title"].lower() for g in guidance)


# ===========================================================================
# Legacy FinanceCognition Tests
# ===========================================================================

def test_cognition_recurring_detection_and_behavior_pattern() -> None:
    cognition = FinanceCognition()
    tx = [
        {"amount_cents": -1000, "merchant": "StreamFlix", "ts": "2026-01-01T00:00:00+00:00", "direction": "expense"},
        {"amount_cents": -1100, "merchant": "StreamFlix", "ts": "2026-02-01T00:00:00+00:00", "direction": "expense"},
        {"amount_cents": -1200, "merchant": "StreamFlix", "ts": "2026-03-01T00:00:00+00:00", "direction": "expense"},
        {"amount_cents": -9000, "merchant": "Mall", "ts": "2026-03-15T00:00:00+00:00", "direction": "expense"},
    ]
    recurring = cognition.detect_recurring_expenses(tx)
    assert recurring[0]["merchant"] == "streamflix"

    insights = cognition.analyze(tx, paycheck_days=[15])
    patterns = {item["pattern"] for item in insights}
    assert "spending_drift" in patterns
    assert "post_payday_spike" in patterns


# ===========================================================================
# Traceable / Explainable (Section 8 of spec)
# ===========================================================================

def test_all_alerts_have_source_rule() -> None:
    engine = FinanceAlertEngine()
    snapshot = {
        "budgets": [{"id": "b1", "name": "Test", "category_id": "test", "amount_limit_cents": 100}],
        "transactions": [{"amount_cents": -200, "category_id": "test", "direction": "expense"}],
    }
    alerts = engine.evaluate(snapshot)
    for alert in alerts:
        assert "source_rule" in alert and alert["source_rule"]
        assert "severity" in alert


def test_all_insights_have_data_source() -> None:
    engine = FinanceInsightEngine()
    transactions = [
        {"amount_cents": -5000, "direction": "expense", "category_id": "dining", "merchant": "Cafe", "transaction_date": "2026-03-10"},
    ]
    insights = engine.analyze(transactions)
    for insight in insights:
        assert "data_source" in insight and insight["data_source"]


def test_all_guidance_has_traceable_basis() -> None:
    engine = FinanceGuidanceEngine()
    guidance = engine.generate(
        transactions=[{"amount_cents": -30000, "direction": "expense", "category_id": "dining"}],
        budgets=[{"id": "b1", "name": "Dining", "category_id": "dining", "amount_limit_cents": 20000}],
    )
    for g in guidance:
        assert "traceable_basis" in g and g["traceable_basis"]
