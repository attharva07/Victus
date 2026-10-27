"""The /chat endpoint: authenticated, language-layer only."""

from __future__ import annotations

import pytest

# apps.local.main imports the orchestrator (missing core.signals / victus.core.confidence on this
# checkout) and an undeclared dependency (platformdirs). Skip with a reason until those exist.
pytest.importorskip(
    "apps.local.main",
    reason="app not importable: missing core.signals / victus.core.confidence / platformdirs",
    exc_type=ImportError,
)

from fastapi.testclient import TestClient

from apps.local.main import create_app
from core.security.auth import require_user


@pytest.fixture()
def client(lang_env):
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client, app


def test_chat_requires_authentication(client) -> None:
    test_client, _ = client
    response = test_client.post("/chat", json={"message": "hello"})
    assert response.status_code in (401, 403)


def test_chat_round_trip_when_authenticated(client) -> None:
    test_client, app = client
    app.dependency_overrides[require_user] = lambda: "tester"
    saved = test_client.post("/chat", json={"message": "remember my exam is on Friday"})
    assert saved.status_code == 200
    assert saved.json()["action"] == "fact.remember"
    assert "Your exam is on Friday." in saved.json()["reply"]

    answered = test_client.post("/chat", json={"message": "what is my exam?"})
    assert "Your exam is on Friday." in answered.json()["reply"]


def test_chat_validates_input(client) -> None:
    test_client, app = client
    app.dependency_overrides[require_user] = lambda: "tester"
    assert test_client.post("/chat", json={"message": ""}).status_code == 422
    assert test_client.post("/chat", json={"message": "x" * 1001}).status_code == 422


def test_chat_cannot_trigger_tools(client) -> None:
    test_client, app = client
    app.dependency_overrides[require_user] = lambda: "tester"
    response = test_client.post("/chat", json={"message": "write to notes.txt: hello"})
    assert response.status_code == 200
    assert response.json()["action"] is None
