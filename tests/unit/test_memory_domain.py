"""
Unit tests for the Memory domain.

Covers: entities, schemas, policy, service, handlers, and API routes.
"""
from __future__ import annotations

import importlib
from pathlib import Path

import bcrypt
import pytest
from fastapi.testclient import TestClient

from core.security.bootstrap_store import set_bootstrap


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def memory_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    import core.storage.db as db_module
    import core.memory.service as svc_module
    import core.memory.store as store_module

    db_module._DB_INITIALIZED.clear()
    importlib.reload(db_module)
    importlib.reload(store_module)
    svc_module = importlib.reload(svc_module)
    return svc_module


@pytest.fixture()
def api_client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> TestClient:
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    password_hash = bcrypt.hashpw(b"testpass", bcrypt.gensalt()).decode()
    set_bootstrap(password_hash, "test-secret")
    local_main = importlib.reload(importlib.import_module("apps.local.main"))
    return TestClient(local_main.create_app())


def _auth(client: TestClient) -> dict[str, str]:
    login = client.post("/login", json={"username": "admin", "password": "testpass"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


# ---------------------------------------------------------------------------
# A. Entities
# ---------------------------------------------------------------------------


def test_memory_entity_is_frozen() -> None:
    from core.memory.entities import Memory

    m = Memory(
        id="m1",
        ts="2026-01-01T00:00:00Z",
        type="note",
        tags=["work"],
        source="user",
        content="test content",
        importance=5,
        confidence=0.9,
        sensitivity="internal",
    )
    assert m.content == "test content"
    with pytest.raises((AttributeError, TypeError)):
        m.content = "changed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# B. Schemas
# ---------------------------------------------------------------------------


def test_memory_write_schema_accepts_valid_input() -> None:
    from core.memory.schemas import MemoryWrite

    w = MemoryWrite(content="hello world", type="note", sensitivity="internal")
    assert w.content == "hello world"
    assert w.sensitivity == "internal"


def test_memory_write_schema_rejects_invalid_type() -> None:
    from core.memory.schemas import MemoryWrite
    import pydantic

    with pytest.raises((pydantic.ValidationError, ValueError)):
        MemoryWrite(content="x", type="invalid_type")


def test_memory_write_schema_rejects_invalid_sensitivity() -> None:
    from core.memory.schemas import MemoryWrite
    import pydantic

    with pytest.raises((pydantic.ValidationError, ValueError)):
        MemoryWrite(content="x", sensitivity="topsecret")


def test_memory_write_schema_rejects_empty_content() -> None:
    from core.memory.schemas import MemoryWrite
    import pydantic

    with pytest.raises((pydantic.ValidationError, ValueError)):
        MemoryWrite(content="")


# ---------------------------------------------------------------------------
# C. Policy
# ---------------------------------------------------------------------------


def test_memory_policy_allows_valid_actions() -> None:
    from core.memory.policy import enforce_memory_policy

    for action in ("write_memory", "search_memories", "list_recent", "get_memory_by_id", "delete_memory"):
        enforce_memory_policy(action)  # must not raise


def test_memory_policy_blocks_unknown_action() -> None:
    from core.memory.policy import MemoryPolicyError, enforce_memory_policy

    with pytest.raises(MemoryPolicyError):
        enforce_memory_policy("drop_all_memories")


# ---------------------------------------------------------------------------
# D. Service — write / retrieve / delete
# ---------------------------------------------------------------------------


def test_write_and_retrieve_memory(memory_env) -> None:
    memory_id = memory_env.add_memory(
        content="buy coffee beans",
        type="note",
        tags=["shopping"],
        source="test",
    )
    assert memory_id

    results = memory_env.search_memories(query="coffee", tags=None, limit=10)
    assert any(r["id"] == memory_id for r in results)


def test_search_by_tag(memory_env) -> None:
    memory_env.add_memory(content="team standup at 9am", type="event", tags=["work", "meeting"], source="test")
    memory_env.add_memory(content="buy groceries", type="note", tags=["personal"], source="test")

    results = memory_env.search_memories(query="", tags=["work"], limit=10)
    contents = [r["content"] for r in results]
    assert any("standup" in c for c in contents)


def test_list_recent(memory_env) -> None:
    memory_env.add_memory(content="first memory", type="note", source="test")
    memory_env.add_memory(content="second memory", type="note", source="test")
    results = memory_env.list_recent(limit=10)
    assert len(results) >= 2


def test_delete_memory(memory_env) -> None:
    memory_id = memory_env.add_memory(content="to be deleted", type="note", source="test")
    deleted = memory_env.delete_memory(memory_id)
    assert deleted is True

    results = memory_env.search_memories(query="to be deleted", tags=None, limit=10)
    assert not any(r["id"] == memory_id for r in results)


def test_delete_nonexistent_returns_false(memory_env) -> None:
    result = memory_env.delete_memory("nonexistent-id-xyz")
    assert result is False


def test_sensitivity_filtering_internal(memory_env) -> None:
    memory_env.add_memory(content="secret config", type="note", source="test", sensitivity="sensitive")
    results = memory_env.search_memories(
        query="secret config", tags=None, limit=10, allowed_sensitivity=["internal"]
    )
    # "sensitive" rank > "internal", so it should be filtered out
    assert len(results) == 0


def test_sensitivity_filtering_allows_matching_level(memory_env) -> None:
    memory_env.add_memory(content="public announcement", type="note", source="test", sensitivity="public")
    results = memory_env.search_memories(
        query="public announcement", tags=None, limit=10, allowed_sensitivity=["internal"]
    )
    # "public" rank <= "internal", so it should pass through
    assert len(results) >= 1


def test_empty_content_rejected(memory_env) -> None:
    with pytest.raises(ValueError):
        memory_env.add_memory(content="", type="note", source="test")


def test_invalid_sensitivity_rejected(memory_env) -> None:
    with pytest.raises(ValueError):
        memory_env.add_memory(content="x", type="note", source="test", sensitivity="top_secret")


# ---------------------------------------------------------------------------
# E. Handlers
# ---------------------------------------------------------------------------


def test_create_note_handler(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    from core.domains.memory import handlers
    importlib.reload(handlers)

    result = handlers.create_note_handler(
        {"content": "buy milk", "tags": ["grocery"], "sensitivity": "internal"},
        {"user_id": "test-user"},
    )
    assert result["memory_id"]
    assert result["message"]


def test_search_handler_requires_query(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    from core.domains.memory import handlers
    importlib.reload(handlers)

    with pytest.raises(ValueError, match="query"):
        handlers.search_handler({"query": ""}, {})


def test_list_recent_handler(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    from core.domains.memory import handlers
    importlib.reload(handlers)

    handlers.create_note_handler({"content": "entry 1"}, {"user_id": "u1"})
    result = handlers.list_recent_handler({"limit": 10}, {})
    assert result["count"] >= 1
    assert isinstance(result["results"], list)


def test_get_memory_handler_found(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    from core.domains.memory import handlers
    importlib.reload(handlers)

    created = handlers.create_note_handler({"content": "findable note"}, {"user_id": "u1"})
    result = handlers.get_memory_handler({"memory_id": created["memory_id"]}, {})
    assert result["found"] is True
    assert result["memory"]["content"] == "findable note"


def test_get_memory_handler_not_found(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    from core.domains.memory import handlers
    importlib.reload(handlers)

    result = handlers.get_memory_handler({"memory_id": "nonexistent-xyz"}, {})
    assert result["found"] is False


def test_delete_memory_handler(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    from core.domains.memory import handlers
    importlib.reload(handlers)

    created = handlers.create_note_handler({"content": "to delete"}, {"user_id": "u1"})
    result = handlers.delete_memory_handler({"memory_id": created["memory_id"]}, {})
    assert result["deleted"] is True


# ---------------------------------------------------------------------------
# F. API Routes
# ---------------------------------------------------------------------------


def test_memory_routes_require_auth(api_client: TestClient) -> None:
    assert api_client.post("/memory/add", json={"content": "x"}).status_code == 401
    assert api_client.get("/memory/search", params={"q": "x"}).status_code == 401
    assert api_client.get("/memory/list").status_code == 401


def test_memory_add_search_list_delete_flow(api_client: TestClient) -> None:
    headers = _auth(api_client)

    # Add
    add_resp = api_client.post(
        "/memory/add",
        json={"content": "remember the standup at 9am", "type": "event", "tags": ["work"]},
        headers=headers,
    )
    assert add_resp.status_code == 200
    memory_id = add_resp.json()["id"]
    assert memory_id

    # Search
    search_resp = api_client.get(
        "/memory/search",
        params={"q": "standup", "limit": 5},
        headers=headers,
    )
    assert search_resp.status_code == 200
    results = search_resp.json()["results"]
    assert any(r["id"] == memory_id for r in results)

    # List
    list_resp = api_client.get("/memory/list", headers=headers)
    assert list_resp.status_code == 200
    assert isinstance(list_resp.json()["results"], list)
    assert len(list_resp.json()["results"]) >= 1

    # Delete
    del_resp = api_client.delete(f"/memory/{memory_id}", headers=headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted"] is True


def test_memory_add_rejects_empty_content(api_client: TestClient) -> None:
    headers = _auth(api_client)
    resp = api_client.post("/memory/add", json={"content": ""}, headers=headers)
    assert resp.status_code in (400, 422)
