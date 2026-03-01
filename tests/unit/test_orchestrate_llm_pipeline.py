from __future__ import annotations

import importlib
import json
from pathlib import Path

import bcrypt
import pytest
from fastapi.testclient import TestClient

from core.memory.service import list_recent
from core.security.bootstrap_store import set_bootstrap


def _client_with_llm(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> TestClient:
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("VICTUS_LLM_ENABLED", "true")
    monkeypatch.setenv("VICTUS_LLM_PROVIDER", "ollama")
    password_hash = bcrypt.hashpw(b"testpass", bcrypt.gensalt()).decode("utf-8")
    set_bootstrap(password_hash, "test-secret")
    local_main = importlib.reload(importlib.import_module("apps.local.main"))
    return TestClient(local_main.create_app())


def _auth_headers(client: TestClient) -> dict[str, str]:
    login = client.post("/login", json={"username": "admin", "password": "testpass"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_orchestrate_llm_fallback_returns_intent_not_unknown(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("adapters.llm.provider._http_get_json", lambda *_args, **_kwargs: {"models": [{"name": "mistral"}]})

    def _fake_generate(_url: str, payload: dict[str, object], timeout: int = 10) -> dict[str, object]:
        _ = timeout
        assert payload["model"] == "mistral"
        return {
            "response": json.dumps(
                {
                    "action": "memory.add",
                    "parameters": {"content": "got starbucks today"},
                    "confidence": 0.6,
                }
            )
        }

    monkeypatch.setattr("adapters.llm.provider._http_json", _fake_generate)
    client = _client_with_llm(monkeypatch, tmp_path)
    response = client.post("/orchestrate", json={"text": "got starbucks today"}, headers=_auth_headers(client))
    assert response.status_code == 200
    payload = response.json()
    assert "error" not in payload
    assert payload["intent"]["action"] in {"memory.add", "noop"}
    assert payload["mode"] in {"llm_proposal", "deterministic"}


def test_orchestrate_force_llm_context(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("adapters.llm.provider._http_get_json", lambda *_args, **_kwargs: {"models": [{"name": "mistral"}]})
    monkeypatch.setattr(
        "adapters.llm.provider._http_json",
        lambda *_args, **_kwargs: {
            "response": json.dumps(
                {
                    "action": "memory.add",
                    "parameters": {"content": "force llm"},
                    "confidence": 0.5,
                }
            )
        },
    )
    client = _client_with_llm(monkeypatch, tmp_path)
    response = client.post(
        "/orchestrate",
        json={"text": "remember hello", "context": {"force_llm": True}},
        headers=_auth_headers(client),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "llm_proposal"


def test_orchestrate_execute_confident_memory_add(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("VICTUS_LLM_ALLOW_AUTOEXEC", "true")
    monkeypatch.setattr("adapters.llm.provider._http_get_json", lambda *_args, **_kwargs: {"models": [{"name": "mistral"}]})
    monkeypatch.setattr(
        "adapters.llm.provider._http_json",
        lambda *_args, **_kwargs: {
            "response": json.dumps(
                {
                    "action": "memory.add",
                    "parameters": {"content": "paid for lunch"},
                    "confidence": 0.9,
                }
            )
        },
    )
    client = _client_with_llm(monkeypatch, tmp_path)
    response = client.post("/orchestrate", json={"text": "paid for lunch"}, headers=_auth_headers(client))
    assert response.status_code == 200
    payload = response.json()
    assert payload["executed"] is True
    memories = list_recent(limit=10)
    assert any(memory["content"] == "paid for lunch" for memory in memories)


def test_orchestrate_does_not_autoexecute_when_disabled(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("VICTUS_LLM_ALLOW_AUTOEXEC", "false")
    monkeypatch.setattr("adapters.llm.provider._http_get_json", lambda *_args, **_kwargs: {"models": [{"name": "mistral"}]})
    monkeypatch.setattr(
        "adapters.llm.provider._http_json",
        lambda *_args, **_kwargs: {
            "response": json.dumps(
                {
                    "action": "memory.add",
                    "parameters": {"content": "should need approval"},
                    "confidence": 0.95,
                }
            )
        },
    )
    client = _client_with_llm(monkeypatch, tmp_path)
    response = client.post("/orchestrate", json={"text": "should need approval"}, headers=_auth_headers(client))
    assert response.status_code == 200
    payload = response.json()
    assert payload["executed"] is False
    assert payload["proposed_action"]["action"] == "memory.add"
    memories = list_recent(limit=10)
    assert not any(memory["content"] == "should need approval" for memory in memories)


def test_model_selection_priority(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "adapters.llm.provider._http_get_json",
        lambda *_args, **_kwargs: {"models": [{"name": "llama3.1:8b"}, {"name": "mistral"}]},
    )
    monkeypatch.setattr(
        "adapters.llm.provider._http_json",
        lambda *_args, **_kwargs: {
            "response": json.dumps(
                {
                    "action": "noop",
                    "parameters": {},
                    "confidence": 0.5,
                }
            )
        },
    )
    client = _client_with_llm(monkeypatch, tmp_path)
    headers = _auth_headers(client)
    debug = client.get("/debug/orchestrator", headers=headers)
    assert debug.status_code == 200
    before = debug.json()
    assert before["selected_model"] is None

    response = client.post("/orchestrate", json={"text": "something uncertain"}, headers=headers)
    assert response.status_code == 200

    after = client.get("/debug/orchestrator", headers=headers).json()
    assert after["selected_model"] == "mistral"
