import json

import pytest

from victus.core.cli import main
from victus.core.cli.constants import EXIT_STATE_CONFLICT, EXIT_VALIDATION
from victus.core.memory import service, store
from victus.core.memory.service import MemoryServiceError


@pytest.fixture(autouse=True)
def temp_paths(tmp_path, monkeypatch):
    mem_path = tmp_path / "store.json"
    prop_path = tmp_path / "proposals"
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(json.dumps({"secret_patterns": []}))

    monkeypatch.setattr(store, "DEFAULT_STORE_PATH", mem_path)
    monkeypatch.setattr(store, "MEMORY_PATH", mem_path)
    from victus.core.memory import proposals

    monkeypatch.setattr(proposals, "PROPOSALS_PATH", prop_path)
    monkeypatch.setattr(proposals, "POLICY_PATH", policy_path)
    monkeypatch.setattr(proposals, "STORE_PATH", mem_path)

    yield


def test_memory_cannot_be_written_without_approval():
    with pytest.raises(store.MemoryStoreError):
        store.append_memory({
            "id": "mem_test",
            "domain": "project",
            "memory_type": "project_context",
            "content": "x",
            "source": "direct",
            "ts": "",
            "risk_flags": [],
            "explicit_user_request": True,
        })


def test_invalid_category_rejected_and_logs_failure(tmp_path):
    exit_code = main.main([
        "memory",
        "propose",
        "--category",
        "invalid",
        "--content",
        "not allowed",
    ])
    assert exit_code == EXIT_VALIDATION


def test_approve_creates_memory_record():
    proposal_id = service.propose_memory("project_context", "content", True, [])
    memory_id = service.approve_memory(proposal_id)
    records = store.list_memory()
    assert any(r.get("id") == memory_id for r in records)


def test_approve_non_pending_fails():
    proposal_id = service.propose_memory("project_context", "content", True, [])
    service.approve_memory(proposal_id)
    with pytest.raises(MemoryServiceError):
        service.approve_memory(proposal_id)
