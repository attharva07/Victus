import json

import pytest

from victus.core.cli import main
from victus.core.cli.constants import EXIT_STATE_CONFLICT, EXIT_VALIDATION
from victus.core.memory import service, store
from victus.core.memory.service import MemoryServiceError


@pytest.fixture(autouse=True)
def temp_paths(tmp_path, monkeypatch):
    mem_path = tmp_path / "memory.jsonl"
    prop_path = tmp_path / "proposals.jsonl"
    fail_path = tmp_path / "failures.jsonl"
    report_dir = tmp_path / "reports"

    monkeypatch.setattr(store, "MEMORY_PATH", mem_path)
    from victus.core.memory import proposals
    monkeypatch.setattr(proposals, "PROPOSALS_PATH", prop_path)
    from victus.core.failures import store as failure_store
    monkeypatch.setattr(failure_store, "FAILURES_PATH", fail_path)
    from victus.core.failures import summarize
    monkeypatch.setattr(summarize, "REPORTS_DIR", report_dir)

    yield


def test_memory_cannot_be_written_without_approval():
    with pytest.raises(store.MemoryStoreError):
        store.append_memory({"id": "mem_test", "category": "project_state", "content": "x", "source": "direct", "created_at": "", "confidence": "medium", "tags": []})


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
    from victus.core.failures import store as failure_store

    failures = failure_store.list_failures()
    assert len(failures) == 1
    assert "Category is not allowed" in failures[0].why_it_failed


def test_approve_creates_memory_record():
    proposal_id = service.propose_memory("project_state", "content", "high", [])
    memory_id = service.approve_memory(proposal_id)
    records = store.list_memory()
    assert any(r.id == memory_id for r in records)


def test_approve_non_pending_fails():
    proposal_id = service.propose_memory("project_state", "content", "high", [])
    service.approve_memory(proposal_id)
    with pytest.raises(MemoryServiceError):
        service.approve_memory(proposal_id)
