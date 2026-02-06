from __future__ import annotations

import importlib
from pathlib import Path

import bcrypt
import pytest
from fastapi.testclient import TestClient

from core.security.bootstrap_store import is_bootstrapped, set_bootstrap, verify_admin_password


def _client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> TestClient:
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    local_main = importlib.reload(importlib.import_module("apps.local.main"))
    return TestClient(local_main.create_app())


def test_bootstrap_state_fresh_db(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    assert is_bootstrapped() is False


def test_bootstrap_state_after_set(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    password_hash = bcrypt.hashpw(b"strong-password", bcrypt.gensalt()).decode("utf-8")
    set_bootstrap(password_hash, "secret")
    assert is_bootstrapped() is True


def test_verify_admin_password(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    password_hash = bcrypt.hashpw(b"strong-password", bcrypt.gensalt()).decode("utf-8")
    set_bootstrap(password_hash, "secret")
    assert verify_admin_password("strong-password") is True
    assert verify_admin_password("wrong-password") is False


def test_login_rejected_when_not_bootstrapped(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client = _client(monkeypatch, tmp_path)
    response = client.post("/login", json={"username": "admin", "password": "password"})
    assert response.status_code == 400
    payload = response.json()
    assert payload["detail"]["error"] == "not_bootstrapped"


def test_login_succeeds_after_bootstrap(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    password_hash = bcrypt.hashpw(b"strong-password", bcrypt.gensalt()).decode("utf-8")
    set_bootstrap(password_hash, "secret")
    client = _client(monkeypatch, tmp_path)
    response = client.post("/login", json={"username": "admin", "password": "strong-password"})
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_bootstrap_init_flow(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = _client(monkeypatch, tmp_path)

    status_before = client.get("/bootstrap/status")
    assert status_before.status_code == 200
    assert status_before.json()["bootstrapped"] is False

    init_response = client.post(
        "/bootstrap/init",
        json={"username": "admin", "password": "super-strong-123"},
    )
    assert init_response.status_code == 200
    assert init_response.json() == {"ok": True, "bootstrapped": True}

    status_after = client.get("/bootstrap/status")
    assert status_after.status_code == 200
    assert status_after.json()["bootstrapped"] is True


def test_bootstrap_init_rejected_when_already_bootstrapped(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client = _client(monkeypatch, tmp_path)
    first = client.post(
        "/bootstrap/init",
        json={"username": "admin", "password": "super-strong-123"},
    )
    assert first.status_code == 200

    second = client.post(
        "/bootstrap/init",
        json={"username": "admin", "password": "another-strong-123"},
    )
    assert second.status_code == 409
    payload = second.json()
    assert payload["detail"]["error"] == "already_bootstrapped"
