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
    init = client.post("/bootstrap/init", json={"username": "admin", "password": password})
    assert init.status_code == 200

    login = client.post("/login", json={"username": "admin", "password": password})
    assert login.status_code == 200
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_backend_routes_smoke(client: TestClient) -> None:
    headers = _auth_headers(client)

    assert client.get("/health").status_code == 200
    assert client.get("/bootstrap/status").status_code == 200
    assert client.get("/me", headers=headers).status_code == 200

    assert client.post("/orchestrate", json={"text": "hello"}, headers=headers).status_code == 200

    add_memory = client.post(
        "/memory/add",
        json={"content": "remember this", "type": "note", "confidence": 0.9, "importance": 5},
        headers=headers,
    )
    assert add_memory.status_code == 200
    memory_id = add_memory.json()["id"]

    assert client.get("/memory/search?q=remember", headers=headers).status_code == 200
    assert client.get("/memory/list", headers=headers).status_code == 200
    assert client.delete(f"/memory/{memory_id}", headers=headers).status_code == 200

    assert (
        client.post(
            "/finance/add",
            json={"amount": 10.5, "category": "test", "currency": "USD"},
            headers=headers,
        ).status_code
        == 200
    )
    assert client.get("/finance/list", headers=headers).status_code == 200
    assert client.get("/finance/summary", headers=headers).status_code == 200

    assert client.get("/files/list", headers=headers).status_code == 200
    assert (
        client.post(
            "/files/write",
            json={"path": "notes/test.txt", "content": "ok", "mode": "overwrite"},
            headers=headers,
        ).status_code
        == 200
    )
    assert client.get("/files/read?path=notes/test.txt", headers=headers).status_code == 200

    assert client.get("/camera/status", headers=headers).status_code == 200
    assert client.post("/camera/capture", json={}, headers=headers).status_code == 200
    assert client.post("/camera/recognize", json={}, headers=headers).status_code == 200
