from typing import List

from ..failures.service import log_failure
from ..util.ids import generate_id
from ..util.time import now_iso
from .models import CONFIDENCE_LEVELS
from .policy import validate_memory_proposal
from .proposals import ProposalNotFound, create_proposal, get, list_proposals, revise as revise_proposal, update_status
from .store import append_memory, MemoryStoreError


class MemoryServiceError(Exception):
    pass


def propose_memory(category: str, content: str, confidence: str, tags: List[str]):
    ok, reason = validate_memory_proposal(category, content)
    if not ok:
        log_failure(
            context="memory.propose",
            what_failed="Memory proposal rejected",
            why_it_failed=reason,
            expected_behavior="Reject invalid categories or denied content",
            severity="medium",
        )
        raise MemoryServiceError(reason)
    if confidence not in CONFIDENCE_LEVELS:
        confidence = "medium"
    return create_proposal(category, content, confidence, tags)


def approve_memory(proposal_id: str) -> str:
    proposal = get(proposal_id)
    if proposal.status != "pending":
        raise MemoryServiceError("Proposal is not pending")
    memory_id = generate_id("mem")
    record = {
        "id": memory_id,
        "category": proposal.category,
        "content": proposal.content,
        "source": "user_approved",
        "created_at": now_iso(),
        "confidence": proposal.confidence,
        "tags": proposal.tags,
    }
    append_memory(record, authorized=True)
    update_status(proposal_id, "approved")
    return memory_id


def reject_memory(proposal_id: str) -> None:
    proposal = get(proposal_id)
    if proposal.status != "pending":
        raise MemoryServiceError("Proposal is not pending")
    update_status(proposal_id, "rejected")


def revise_memory(proposal_id: str, new_content: str) -> None:
    proposal = get(proposal_id)
    if proposal.status != "pending":
        raise MemoryServiceError("Proposal is not pending")
    revise_proposal(proposal_id, new_content)
    update_status(proposal_id, "revised")


def list_memory_proposals(status: str = None, limit: int = None):
    return list_proposals(status=status, limit=limit)
