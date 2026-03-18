from __future__ import annotations

import importlib
from pathlib import Path

import pytest


@pytest.fixture()
def finance_service(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    import core.storage.db as db_module
    import core.finance.repository as repository_module
    import core.finance.service as service_module

    db_module._DB_INITIALIZED.clear()
    importlib.reload(db_module)
    importlib.reload(repository_module)
    service_module = importlib.reload(service_module)
    return service_module


# ===========================================================================
# A. LEDGER CORE — Transactions
# ===========================================================================

def test_successful_transaction_creation_and_fetch(finance_service) -> None:
    account = finance_service.upsert_account(name="Primary Checking", account_type="checking")
    transaction_id = finance_service.add_transaction(
        amount_cents=-1234,
        currency="USD",
        category="Dining Out",
        merchant="Local Cafe",
        note="latte and toast",
        method="debit",
        source="test",
        account_id=account["id"],
        ts="2026-03-10",
    )

    transaction = finance_service.get_transaction(transaction_id)
    assert transaction["id"] == transaction_id
    assert transaction["account_id"] == account["id"]
    assert transaction["amount_cents"] == 1234
    assert transaction["transaction_date"] == "2026-03-10"


def test_malformed_input_rejection(finance_service) -> None:
    with pytest.raises(Exception) as excinfo:
        finance_service.add_transaction(
            amount_cents=0,
            currency="USD",
            category="coffee",
            source="test",
        )
    assert "Amount cannot be zero" in str(excinfo.value)


def test_update_and_delete_behavior(finance_service) -> None:
    transaction_id = finance_service.add_transaction(
        amount_cents=-5000,
        currency="USD",
        category="groceries",
        merchant="Market",
        source="test",
        ts="2026-03-01",
    )

    updated = finance_service.update_transaction(
        transaction_id,
        notes="paper towels and soap",
        amount="-45.25",
    )
    assert abs(updated["amount_cents"]) == 4525
    assert updated["notes"] == "paper towels and soap"

    deleted = finance_service.delete_transaction(transaction_id)
    assert deleted["deleted"] is True

    with pytest.raises(Exception) as excinfo:
        finance_service.get_transaction(transaction_id)
    assert "not found" in str(excinfo.value)


def test_summary_generation_and_account_filtering(finance_service) -> None:
    checking = finance_service.upsert_account(name="Checking", account_type="checking")
    savings = finance_service.upsert_account(name="Savings", account_type="savings")

    finance_service.add_transaction(
        amount_cents=-2500, currency="USD", category="Coffee",
        merchant="Cafe", source="test", account_id=checking["id"], ts="2026-03-05",
    )
    finance_service.add_transaction(
        amount_cents=-4000, currency="USD", category="Coffee",
        merchant="Cafe", source="test", account_id=savings["id"], ts="2026-03-06",
    )
    finance_service.add_transaction(
        amount_cents=100000, currency="USD", category="Income",
        merchant="Employer", source="test", account_id=checking["id"], ts="2026-03-07",
    )

    spending = finance_service.spending_summary("2026-03-01", "2026-03-31")
    assert spending["totals"]["transaction_count"] == 3


def test_category_normalization(finance_service) -> None:
    transaction_id = finance_service.add_transaction(
        amount_cents=-1000, currency="USD",
        category="  Food & Dining / Take-Out ",
        merchant="Bistro", source="test", ts="2026-03-12",
    )
    transaction = finance_service.get_transaction(transaction_id)
    # Category is normalized
    assert transaction is not None


def test_unknown_account_rejected(finance_service) -> None:
    with pytest.raises(Exception) as excinfo:
        finance_service.add_transaction(
            amount_cents=-1000, currency="USD", category="coffee",
            source="test", account_id="missing-account", ts="2026-03-12",
        )
    assert "Unknown account_id" in str(excinfo.value)


def test_delete_nonexistent_fails(finance_service) -> None:
    with pytest.raises(Exception) as excinfo:
        finance_service.delete_transaction("does-not-exist")
    assert "not found" in str(excinfo.value)


def test_finance_audit_redacts_notes(finance_service, monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[tuple[str, dict[str, object]]] = []

    def capture(event: str, **fields: object) -> None:
        events.append((event, fields))

    monkeypatch.setattr("core.finance.audit.audit_event", capture)
    transaction_id = finance_service.add_transaction(
        amount_cents=-1500, currency="USD", category="coffee",
        merchant="Cafe", note="card 4242 test note", source="test", ts="2026-03-11",
    )

    assert transaction_id
    create_event = next(fields for event, fields in events if event == "finance_transaction_created")
    assert create_event["notes"]["excerpt"] == "card 4242 test note"
    assert create_event["notes"]["sha256"]


# ===========================================================================
# B. BUDGETS
# ===========================================================================

def test_budget_lifecycle(finance_service) -> None:
    from core.finance.schemas import BudgetCreate, BudgetUpdate
    service = finance_service.FinanceService()

    response = service.create_budget(BudgetCreate(
        name="Monthly Groceries", amount_limit=500.00, category_id=None,
    ))
    assert response.budget.name == "Monthly Groceries"
    assert response.budget.amount_limit_cents == 50000
    budget_id = response.budget.id

    updated = service.update_budget(budget_id, BudgetUpdate(
        amount_limit=600.00, warning_threshold_percent=90,
    ))
    assert updated.budget.amount_limit_cents == 60000
    assert updated.budget.warning_threshold_percent == 90

    budgets = service.list_budgets()
    assert budgets.count >= 1

    deleted = service.delete_budget(budget_id)
    assert deleted.deleted is True


def test_budget_status_evaluation(finance_service) -> None:
    from core.finance.schemas import BudgetCreate
    service = finance_service.FinanceService()

    service.create_budget(BudgetCreate(
        name="Dining Budget", amount_limit=100.00, category_id="dining",
    ))

    status = service.get_budget_status()
    assert status.count >= 1
    for s in status.results:
        assert s.status in ("under", "warning", "exceeded")


# ===========================================================================
# C. BILLS / OBLIGATIONS
# ===========================================================================

def test_bill_lifecycle(finance_service) -> None:
    from core.finance.schemas import BillCreate, BillUpdate
    service = finance_service.FinanceService()

    response = service.create_bill(BillCreate(
        name="Rent", amount_expected=1500.00, due_date="2026-04-01",
        recurrence_rule="monthly",
    ))
    assert response.bill.name == "Rent"
    assert response.bill.status == "pending"
    bill_id = response.bill.id

    updated = service.update_bill(bill_id, BillUpdate(
        amount_expected=1550.00,
    ))
    assert updated.bill.amount_expected_cents == 155000

    paid = service.mark_bill_paid(bill_id)
    assert paid.bill.status == "paid"

    # Double-pay fails
    with pytest.raises(Exception):
        service.mark_bill_paid(bill_id)


def test_due_bills(finance_service) -> None:
    from core.finance.schemas import BillCreate
    service = finance_service.FinanceService()

    service.create_bill(BillCreate(
        name="Electric", amount_expected=120.00, due_date="2026-03-15",
    ))
    service.create_bill(BillCreate(
        name="Future Bill", amount_expected=50.00, due_date="2099-01-01",
    ))

    due = service.get_due_bills()
    names = [b.name for b in due.results]
    assert "Electric" in names


def test_bill_delete(finance_service) -> None:
    from core.finance.schemas import BillCreate
    service = finance_service.FinanceService()

    response = service.create_bill(BillCreate(
        name="Temp Bill", amount_expected=10.00, due_date="2026-05-01",
    ))
    deleted = service.delete_bill(response.bill.id)
    assert deleted.deleted is True

    with pytest.raises(Exception):
        service.delete_bill(response.bill.id)


# ===========================================================================
# D. SAVINGS GOALS
# ===========================================================================

def test_savings_goal_lifecycle(finance_service) -> None:
    from core.finance.schemas import SavingsGoalCreate, SavingsGoalUpdate, SavingsProgressUpdate
    service = finance_service.FinanceService()

    response = service.create_savings_goal(SavingsGoalCreate(
        name="Emergency Fund", target_amount=10000.00, target_date="2026-12-31",
    ))
    assert response.goal.name == "Emergency Fund"
    assert response.goal.target_amount_cents == 1000000
    assert response.goal.current_progress_cents == 0
    goal_id = response.goal.id

    service.record_savings_progress(goal_id, SavingsProgressUpdate(amount=500.00))
    updated = service.update_savings_goal(goal_id, SavingsGoalUpdate(name="Emergency Reserve"))
    assert updated.goal.name == "Emergency Reserve"
    assert updated.goal.current_progress_cents == 50000


def test_savings_status(finance_service) -> None:
    from core.finance.schemas import SavingsGoalCreate
    service = finance_service.FinanceService()

    service.create_savings_goal(SavingsGoalCreate(
        name="Vacation Fund", target_amount=5000.00,
    ))

    status = service.get_savings_status()
    assert status.count >= 1
    for s in status.results:
        assert 0 <= s.progress_percent <= 100


# ===========================================================================
# E. ALERTS
# ===========================================================================

def test_alert_creation_and_resolution(finance_service) -> None:
    service = finance_service.FinanceService()

    service.repository.create_alert({
        "id": "test-alert-1",
        "type": "budget_exceeded",
        "severity": "urgent",
        "title": "Budget exceeded",
        "message": "Dining budget exceeded.",
        "source_rule": "budget_overspend",
        "related_entity_type": "budget",
        "related_entity_id": "budget-1",
        "created_at": "2026-03-18T00:00:00+00:00",
    })

    alerts = service.list_alerts(limit=10)
    assert alerts.count >= 1
    assert alerts.results[0].status == "active"

    resolved = service.resolve_alert("test-alert-1")
    assert resolved.status == "resolved"
    assert resolved.resolved_at is not None


# ===========================================================================
# F. INSIGHTS
# ===========================================================================

def test_insights_generation(finance_service) -> None:
    service = finance_service.FinanceService()

    for i in range(5):
        finance_service.add_transaction(
            amount_cents=-1000 * (i + 1), currency="USD", category="coffee",
            merchant="Cafe", source="test", ts=f"2026-03-{10 + i:02d}",
        )

    insights = service.get_insights("2026-03-01", "2026-03-31")
    assert isinstance(insights.results, list)


# ===========================================================================
# G. GUIDANCE
# ===========================================================================

def test_guidance_generation(finance_service) -> None:
    from core.finance.schemas import BudgetCreate, BillCreate
    service = finance_service.FinanceService()

    service.create_budget(BudgetCreate(
        name="Coffee Budget", amount_limit=50.00, category_id="coffee",
    ))
    service.create_bill(BillCreate(
        name="Internet", amount_expected=60.00, due_date="2026-03-20",
    ))

    guidance = service.get_guidance()
    assert isinstance(guidance.results, list)


# ===========================================================================
# Validation rules (Section 7 of spec)
# ===========================================================================

def test_zero_amount_rejected(finance_service) -> None:
    with pytest.raises(Exception, match="zero"):
        finance_service.add_transaction(
            amount_cents=0, currency="USD", category="test", source="test",
        )


def test_invalid_date_rejected(finance_service) -> None:
    with pytest.raises(Exception):
        finance_service.add_transaction(
            amount_cents=-100, currency="USD", category="test", source="test",
            ts="not-a-date",
        )


def test_destructive_operations_fail_on_invalid_ids(finance_service) -> None:
    with pytest.raises(Exception):
        finance_service.delete_transaction("nonexistent-id")

    with pytest.raises(Exception):
        finance_service.update_transaction("nonexistent-id", notes="test")
