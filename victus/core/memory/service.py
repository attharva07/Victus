"""Public API for memory proposal flow."""

from __future__ import annotations

from typing import List, Optional

from .policy import MEMORY_TYPES
from .proposals import (
    ProposalNotFound,
    MemoryProposal,
    approve_proposal as _approve_proposal,
    list_proposals,
    save_proposal,
)


class MemoryServiceError(Exception):
    pass


def propose_memory(memory_type: str, content: str, explicit_user_request: bool = True, risk_flags: Optional[List[str]] = None) -> str:
    if memory_type not in MEMORY_TYPES:
        raise MemoryServiceError("Memory type is not allowed")
    proposal = MemoryProposal.create(
        domain=memory_type,
        memory_type=memory_type,
        content=content,
        source="manual_review",
        explicit_user_request=explicit_user_request,
        risk_flags=risk_flags or [],
    )
    save_proposal(proposal)
    return proposal.proposal_id


def approve_memory(proposal_id: str) -> str:
    try:
        return _approve_proposal(proposal_id)
    except PermissionError as exc:
        raise MemoryServiceError(str(exc)) from exc
    except ProposalNotFound as exc:
        raise


def list_memory_proposals():
    return list_proposals()


def reject_memory(proposal_id: str) -> None:
    raise MemoryServiceError("Rejection flow not implemented for manual review")


def revise_memory(proposal_id: str, new_content: str) -> None:
    raise MemoryServiceError("Revision flow not implemented for manual review")
