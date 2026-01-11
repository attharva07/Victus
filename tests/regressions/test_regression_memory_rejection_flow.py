import json

from victus.core.memory import proposals


def test_regression_reject_proposal_sets_review_metadata(tmp_path, monkeypatch):
    proposals_dir = tmp_path / "proposals"
    policy_path = tmp_path / "policy.json"
    store_path = tmp_path / "store.json"
    policy_path.write_text(json.dumps({"secret_patterns": []}))

    monkeypatch.setattr(proposals, "POLICY_PATH", policy_path)
    monkeypatch.setattr(proposals, "STORE_PATH", store_path)

    proposal = proposals.MemoryProposal.create(
        domain="project_context",
        memory_type="project_context",
        content="Keep docs short",
        source="manual_review",
        explicit_user_request=True,
    )
    proposals.save_proposal(proposal, proposals_dir)

    proposals.reject_proposal(proposal.proposal_id, "not applicable", proposals_dir)
    updated = proposals.get_proposal(proposal.proposal_id, proposals_dir)

    assert updated.status == "rejected"
    assert updated.review_notes == "not applicable"
    assert updated.reviewed_ts is not None
