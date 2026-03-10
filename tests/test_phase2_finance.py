from __future__ import annotations

import importlib
from pathlib import Path

import bcrypt
import pytest
from fastapi.testclient import TestClient

from core.orchestrator.deterministic import parse_finance_intent
from core.security.bootstrap_store import set_bootstrap


def _client_with_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> TestClient:
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    password_hash = bcrypt.hashpw(b"testpass", bcrypt.gensalt()).decode("utf-8")
    set_bootstrap(password_hash, "test-secret")
    local_main = importlib.reload(importlib.import_module("apps.local.main"))
    return TestClient(local_main.create_app())


def _auth_headers(client: TestClient) -> dict[str, str]:
    login = client.post("/login", json={"username": "admin", "password": "testpass"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_finance_endpoints_require_auth(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = _client_with_env(monkeypatch, tmp_path)
    response = client.get("/finance/list")
    assert response.status_code == 401


@pytest.mark.parametrize(
    ("utterance", "amount", "category", "merchant"),
    [
        ("spent 3 on coffee", 3.0, "coffee", None),
        ("I spent $3 on coffee at Starbucks", 3.0, "coffee", "starbucks"),
        ("paid 12.50 for groceries", 12.5, "groceries", "groceries"),
        ("add transaction $6 for Starbucks", 6.0, "Starbucks", "Starbucks"),
        ("I spent $6 at Starbucks", 6.0, "Starbucks", "Starbucks"),
        ("log $6 Starbucks", 6.0, "Starbucks", "Starbucks"),
    ],
)
def test_finance_deterministic_parsing(utterance: str, amount: float, category: str, merchant: str | None) -> None:
    intent = parse_finance_intent(utterance)
    assert intent is not None
    assert intent.action == "finance.add_transaction"
    assert intent.parameters["amount"] == amount
    assert intent.parameters["category"] == category
    assert intent.parameters.get("merchant") == merchant
    assert intent.parameters.get("currency") == "USD"
    assert intent.parameters.get("occurred_at")


def test_finance_add_list_summary(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = _client_with_env(monkeypatch, tmp_path)
    headers = _auth_headers(client)
    add_response = client.post(
        "/finance/add",
        json={"amount": 3.25, "currency": "USD", "category": "coffee", "merchant": "Cafe"},
        headers=headers,
    )
    assert add_response.status_code == 200
    transaction_id = add_response.json()["id"]

    list_response = client.get("/finance/list", params={"category": "coffee"}, headers=headers)
    assert list_response.status_code == 200
    transactions = list_response.json()["results"]
    assert any(item["id"] == transaction_id for item in transactions)

    summary_response = client.get("/finance/summary", params={"period": "week"}, headers=headers)
    assert summary_response.status_code == 200
    report = summary_response.json()["report"]
    assert report["totals"]["coffee"] >= 325


def test_finance_intelligence_brief_and_rule_endpoints(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = _client_with_env(monkeypatch, tmp_path)
    headers = _auth_headers(client)

    client.post(
        "/finance/add",
        json={"amount": 120.0, "currency": "USD", "category": "dining", "merchant": "Diner"},
        headers=headers,
    )

    rules_get = client.get("/finance/rules", headers=headers)
    assert rules_get.status_code == 200
    assert "credit_utilization_urgent" in rules_get.json()["rules"]

    rules_set = client.post(
        "/finance/rules",
        json={"rule_key": "budget_category_warning_percent", "threshold_value": 0.7, "enabled": True},
        headers=headers,
    )
    assert rules_set.status_code == 200

    brief = client.post(
        "/finance/intelligence/brief",
        json={
            "cards": [
                {
                    "id": "card-1",
                    "name": "Visa",
                    "credit_limit_cents": 100000,
                    "current_balance_cents": 90000,
                    "due_in_days": 1,
                    "statement_in_days": 2,
                    "autopay_enabled": False,
                }
            ],
            "budget": {"id": "b1", "total_limit_cents": 50000, "categories": {"dining": 10000}},
            "savings_goals": [
                {
                    "id": "goal-1",
                    "name": "Emergency Fund",
                    "monthly_contribution_cents": 20000,
                    "contributed_this_month_cents": 5000,
                    "is_emergency_fund": True,
                    "current_cents": 40000,
                    "emergency_target_cents": 100000,
                }
            ],
            "holdings": [
                {"id": "h1", "symbol": "AAPL", "market_value_cents": 90000, "volatility_score": 0.8}
            ],
            "watchlist": [{"id": "w1", "symbol": "TSLA", "review_in_days": 0}],
            "paycheck_days": [15],
        },
        headers=headers,
    )
    assert brief.status_code == 200
    payload = brief.json()
    assert "alerts" in payload
    assert "recommendations" in payload

    alerts = client.get("/finance/alerts", headers=headers)
    assert alerts.status_code == 200
    assert isinstance(alerts.json()["alerts"], list)

    behavior = client.get("/finance/behavior", headers=headers)
    assert behavior.status_code == 200
    assert isinstance(behavior.json()["behavior_logs"], list)
