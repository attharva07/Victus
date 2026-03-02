from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> TestClient:
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    local_main = importlib.reload(importlib.import_module("apps.local.main"))
    return TestClient(local_main.create_app())


def _auth_headers(client: TestClient) -> dict[str, str]:
    password = "SuperSecurePass123!"
    assert client.post("/bootstrap/init", json={"username": "admin", "password": password}).status_code in {200, 409}
    login = client.post("/login", json={"username": "admin", "password": password})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_v2_accepts_top_level_action_executes(client: TestClient) -> None:
    response = client.post(
        "/orchestrate/v2",
        json={"text": "", "action": "finance.add_transaction", "parameters": {"amount": 6, "category": "coffee"}},
        headers=_auth_headers(client),
    )
    assert response.status_code == 200
    payload = response.json()["orchestrator_result"]
    assert payload["decision"] == "allow"
    assert payload["intent"]["action"] == "finance.add_transaction"
    assert payload["tool_results"]


def test_v2_accepts_nested_intent_action_executes(client: TestClient) -> None:
    response = client.post(
        "/orchestrate/v2",
        json={"text": "", "intent": {"action": "finance.add_transaction", "parameters": {"amount": 7.5, "category": "food"}}},
        headers=_auth_headers(client),
    )
    assert response.status_code == 200
    payload = response.json()["orchestrator_result"]
    assert payload["decision"] == "allow"
    assert payload["intent"]["action"] == "finance.add_transaction"


def test_v2_missing_action_returns_needs_clarification(client: TestClient) -> None:
    response = client.post("/orchestrate/v2", json={"text": "hello there"}, headers=_auth_headers(client))
    assert response.status_code == 200
    payload = response.json()["orchestrator_result"]
    assert payload["decision"] == "needs_clarification"
    assert payload["required_inputs"] == ["action"]


def test_v2_invalid_action_returns_unknown_action_clarification(client: TestClient) -> None:
    response = client.post(
        "/orchestrate/v2",
        json={"text": "", "action": "finance.unknown", "parameters": {}},
        headers=_auth_headers(client),
    )
    assert response.status_code == 200
    payload = response.json()["orchestrator_result"]
    assert payload["decision"] == "needs_clarification"
    assert payload["required_inputs"] == ["action"]
    assert payload["policy"]["reason_code"] == "unknown_action"


def test_v2_heuristic_finance_detects_starbucks_6(client: TestClient) -> None:
    response = client.post(
        "/orchestrate/v2",
        json={"text": "I spent $6 at Starbucks"},
        headers=_auth_headers(client),
    )
    assert response.status_code == 200
    payload = response.json()["orchestrator_result"]
    assert payload["intent"]["action"] == "finance.add_transaction"
    assert payload["decision"] == "allow"


def test_debug_block_only_in_debug_mode(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("VICTUS_DEBUG", raising=False)
    local_main = importlib.reload(importlib.import_module("apps.local.main"))
    client = TestClient(local_main.create_app())
    headers = _auth_headers(client)

    normal = client.post("/orchestrate/v2", json={"text": "I spent $6 at Starbucks"}, headers=headers)
    assert "debug" not in normal.json()

    monkeypatch.setenv("VICTUS_DEBUG", "1")
    local_main_debug = importlib.reload(importlib.import_module("apps.local.main"))
    debug_client = TestClient(local_main_debug.create_app())
    debug_headers = _auth_headers(debug_client)
    debug_response = debug_client.post("/orchestrate/v2", json={"text": "I spent $6 at Starbucks"}, headers=debug_headers)
    assert "debug" in debug_response.json()
