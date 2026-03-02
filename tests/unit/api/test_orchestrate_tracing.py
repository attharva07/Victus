from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from adapters.llm.provider import ProposalResult


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


def test_orchestrate_v2_sets_trace_id_and_debug_toggle(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    headers = _auth_headers(client)

    response = client.post("/orchestrate/v2", json={"text": "hello"}, headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert "trace_id" in payload
    assert payload["orchestrator_result"]["trace_id"] == payload["trace_id"]
    assert "debug" not in payload

    monkeypatch.setenv("VICTUS_DEBUG", "1")
    response_debug = client.post("/orchestrate/v2", json={"text": "hello"}, headers=headers)
    assert response_debug.status_code == 200
    payload_debug = response_debug.json()
    assert "debug" in payload_debug
    assert payload_debug["debug"]["stage_reached"]


@pytest.mark.parametrize(
    ("setup_env", "patch_proposal", "expected_reason"),
    [
        ({}, None, "llm_disabled"),
        ({"VICTUS_LLM_ENABLED": "1"}, ProposalResult(ok=False, reason="boom"), "classifier_exception"),
        (
            {"VICTUS_LLM_ENABLED": "1"},
            ProposalResult(ok=True, action="files.unknown", args={}, confidence=0.7),
            "registry_empty",
        ),
    ],
)
def test_unknown_paths_store_reason(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    setup_env: dict[str, str],
    patch_proposal: ProposalResult | None,
    expected_reason: str,
) -> None:
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    for key, value in setup_env.items():
        monkeypatch.setenv(key, value)

    if patch_proposal is not None:
        from adapters.llm.provider import LLMProvider

        monkeypatch.setattr(LLMProvider, "propose", lambda self, **_kwargs: patch_proposal)

    local_main = importlib.reload(importlib.import_module("apps.local.main"))
    test_client = TestClient(local_main.create_app())
    headers = _auth_headers(test_client)
    trace_id = f"test-{expected_reason}"

    response = test_client.post(
        "/orchestrate",
        json={"text": "this is an unmapped command please do something strange"},
        headers={**headers, "X-Request-ID": trace_id},
    )
    assert response.status_code == 200
    assert response.json()["error"] in {"clarify", "unknown_intent"}

    trace_response = test_client.get(f"/debug/trace/{trace_id}", headers=headers)
    assert trace_response.status_code == 200
    trace = trace_response.json()["trace"]
    assert trace["unknown_reason"] == expected_reason
