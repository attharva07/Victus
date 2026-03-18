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

    importlib.reload(db_module)
    importlib.reload(repository_module)
    service_module = importlib.reload(service_module)
    return service_module


def test_successful_transaction_creation_and_fetch(finance_service) -> None:
    account = finance_service.upsert_account(name="Primary Checking", account_type="checking", institution="Bank")
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
    assert transaction["category"] == "dining_out"
    assert transaction["account_id"] == account["id"]
    assert transaction["amount_cents"] == -1234
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

    with pytest.raises(Exception) as date_exc:
        finance_service.update_transaction("missing", transaction_date="03/10/2026")
    assert "transaction_date must be a valid ISO date" in str(date_exc.value)


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
        category="Household Goods",
        note="paper towels and soap",
        amount="-45.25",
    )
    assert updated["category"] == "household_goods"
    assert updated["amount_cents"] == -4525
    assert updated["note"] == "paper towels and soap"

    deleted = finance_service.delete_transaction(transaction_id)
    assert deleted == {"deleted": True, "transaction_id": transaction_id}

    with pytest.raises(Exception) as excinfo:
        finance_service.get_transaction(transaction_id)
    assert "was not found" in str(excinfo.value)


def test_summary_generation_and_account_filtering(finance_service) -> None:
    checking = finance_service.upsert_account(name="Checking", account_type="checking")
    savings = finance_service.upsert_account(name="Savings", account_type="savings")

    finance_service.add_transaction(
        amount_cents=-2500,
        currency="USD",
        category="Coffee",
        merchant="Cafe",
        source="test",
        account_id=checking["id"],
        ts="2026-03-05",
    )
    finance_service.add_transaction(
        amount_cents=-4000,
        currency="USD",
        category="Coffee",
        merchant="Cafe",
        source="test",
        account_id=savings["id"],
        ts="2026-03-06",
    )
    finance_service.add_transaction(
        amount_cents=100000,
        currency="USD",
        category="Income",
        merchant="Employer",
        source="test",
        account_id=checking["id"],
        ts="2026-03-07",
    )

    spending = finance_service.spending_summary("2026-03-01", "2026-03-31")
    assert spending["totals"]["income_cents"] == 100000
    assert spending["totals"]["expense_cents"] == 6500
    assert spending["by_category"]["coffee"] == 6500
    assert spending["by_account"][checking["id"]] == 2500
    assert spending["by_account"][savings["id"]] == 4000

    account_only = finance_service.spending_summary("2026-03-01", "2026-03-31", account_id=checking["id"])
    assert account_only["totals"]["expense_cents"] == 2500
    assert account_only["by_account"] == {checking["id"]: 2500}

    categories = finance_service.category_summary("2026-03-01", "2026-03-31")
    assert categories["categories"][0] == {"category": "coffee", "expense_cents": 6500}


def test_category_normalization_and_failure_paths(finance_service) -> None:
    transaction_id = finance_service.add_transaction(
        amount_cents=-1000,
        currency="USD",
        category="  Food & Dining / Take-Out ",
        merchant="Bistro",
        source="test",
        ts="2026-03-12",
    )
    transaction = finance_service.get_transaction(transaction_id)
    assert transaction["category"] == "food_and_dining_take_out"

    with pytest.raises(Exception) as missing_account_exc:
        finance_service.add_transaction(
            amount_cents=-1000,
            currency="USD",
            category="coffee",
            source="test",
            account_id="missing-account",
            ts="2026-03-12",
        )
    assert "Unknown account_id" in str(missing_account_exc.value)

    with pytest.raises(Exception) as delete_exc:
        finance_service.delete_transaction("does-not-exist")
    assert "was not found" in str(delete_exc.value)


def test_finance_audit_redacts_notes(finance_service, monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[tuple[str, dict[str, object]]] = []

    def capture(event: str, **fields: object) -> None:
        events.append((event, fields))

    monkeypatch.setattr("core.finance.audit.audit_event", capture)
    transaction_id = finance_service.add_transaction(
        amount_cents=-1500,
        currency="USD",
        category="coffee",
        merchant="Cafe",
        note="card 4242 test note",
        source="test",
        ts="2026-03-11",
    )

    assert transaction_id
    create_event = next(fields for event, fields in events if event == "finance_transaction_created")
    assert create_event["note"]["excerpt"] == "card 4242 test note"
    assert create_event["note"]["sha256"]
