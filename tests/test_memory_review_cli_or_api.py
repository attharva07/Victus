import json

import pytest

from victus.core.memory import proposals, service


@pytest.fixture()
def proposal_paths(tmp_path, monkeypatch):
    proposals_dir = tmp_path / "proposals"
    policy_path = tmp_path / "policy.json"
    store_path = tmp_path / "store.json"
    policy_path.write_text(json.dumps({"secret_patterns": []}))

    monkeypatch.setattr(proposals, "PROPOSALS_PATH", proposals_dir)
    monkeypatch.setattr(proposals, "POLICY_PATH", policy_path)
    monkeypatch.setattr(proposals, "STORE_PATH", store_path)
    yield proposals_dir


def test_memory_review_list_show_approve_reject(proposal_paths):
    proposal_id = service.propose_memory("project_context", "content", True, [])
    proposal = service.show_memory_proposal(proposal_id)
    assert proposal.proposal_id == proposal_id
    assert proposal.status == "new"

    proposals_list = service.list_memory_proposals(status="new")
    assert any(p.proposal_id == proposal_id for p in proposals_list)

    memory_id = service.approve_memory(proposal_id)
    approved = service.show_memory_proposal(proposal_id)
    assert approved.status == "approved"
    assert approved.reviewed_ts is not None

    rejected_id = service.propose_memory("project_context", "other", True, [])
    service.reject_memory(rejected_id, "not needed")
    rejected = service.show_memory_proposal(rejected_id)
    assert rejected.status == "rejected"
    assert rejected.review_notes == "not needed"
