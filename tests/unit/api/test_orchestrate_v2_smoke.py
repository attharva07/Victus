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
    assert client.post("/bootstrap/init", json={"username": "admin", "password": password}).status_code == 200
    login = client.post("/login", json={"username": "admin", "password": password})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_orchestrate_v2_returns_both_outputs_and_consistent_decision(client: TestClient) -> None:
    headers = _auth_headers(client)
    response = client.post(
        "/orchestrate/v2",
        json={"text": "remind me to submit taxes", "profile": {"tone": "friendly", "verbosity": "normal"}},
        headers=headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "orchestrator_result" in payload
    assert "rendered_result" in payload

    orch = payload["orchestrator_result"]
    rendered = payload["rendered_result"]
    assert orch["decision"] == "needs_clarification"
    assert rendered["ui_copy_hints"]["decision"] == orch["decision"]
    assert orch["intent"]["action"] == "productivity.reminder.create"
    assert isinstance(rendered["headline"], str)
