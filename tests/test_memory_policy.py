from victus.core.memory.policy import MemoryPolicy, validate_memory_write
from victus.core.memory.proposals import MemoryProposal


def _proposal(memory_type: str, explicit_user_request: bool = True) -> MemoryProposal:
    return MemoryProposal(
        proposal_id="p-1",
        ts="2024-01-01T00:00:00+00:00",
        domain="demo",
        memory_type=memory_type,
        content="safe content",
        source="manual_review",
        explicit_user_request=explicit_user_request,
        risk_flags=[],
    )


def test_memory_policy_blocks_ephemeral():
    policy = MemoryPolicy(secret_patterns=[])
    ok, reasons = validate_memory_write(_proposal("ephemeral"), policy)
    assert ok is False
    assert any("ephemeral" in reason for reason in reasons)


def test_memory_policy_blocks_sensitive_without_explicit_request():
    policy = MemoryPolicy(secret_patterns=[])
    ok, reasons = validate_memory_write(_proposal("identity_sensitive", explicit_user_request=False), policy)
    assert ok is False
    assert any("explicit" in reason for reason in reasons)


def test_memory_policy_allows_manual_review_safe_type():
    policy = MemoryPolicy(secret_patterns=[])
    ok, reasons = validate_memory_write(_proposal("preference"), policy)
    assert ok is True
    assert reasons == []
