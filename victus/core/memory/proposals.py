from pathlib import Path
from typing import Dict, List, Optional

from ..util.ids import generate_id
from ..util.jsonl import append_jsonl, read_jsonl
from ..util.time import now_iso
from .models import MemoryProposal

PROPOSALS_PATH = Path("data/memory/proposals.jsonl")


class ProposalNotFound(Exception):
    pass


def _rebuild_state() -> Dict[str, MemoryProposal]:
    state: Dict[str, MemoryProposal] = {}
    for event in read_jsonl(PROPOSALS_PATH):
        action = event.get("action")
        proposal_id = event["proposal_id"]
        if action == "create":
            state[proposal_id] = MemoryProposal(**event["data"])
        elif proposal_id in state:
            proposal = state[proposal_id]
            if action == "update_status":
                proposal.status = event["status"]
                proposal.updated_at = event["updated_at"]
            elif action == "revise":
                proposal.history.append(event["history_entry"])
                proposal.content = event["new_content"]
                proposal.updated_at = event["updated_at"]
    return state


def create_proposal(category: str, content: str, confidence: str, tags: List[str]) -> str:
    proposal_id = generate_id("prop")
    proposal = MemoryProposal(
        proposal_id=proposal_id,
        category=category,
        content=content,
        confidence=confidence,
        tags=tags,
        status="pending",
        created_at=now_iso(),
        updated_at=now_iso(),
        history=[],
    )
    append_jsonl(PROPOSALS_PATH, {"action": "create", "proposal_id": proposal_id, "data": proposal.__dict__})
    return proposal_id


def update_status(proposal_id: str, status: str) -> None:
    proposals = _rebuild_state()
    if proposal_id not in proposals:
        raise ProposalNotFound(proposal_id)
    append_jsonl(
        PROPOSALS_PATH,
        {
            "action": "update_status",
            "proposal_id": proposal_id,
            "status": status,
            "updated_at": now_iso(),
        },
    )


def revise(proposal_id: str, new_content: str) -> None:
    proposals = _rebuild_state()
    if proposal_id not in proposals:
        raise ProposalNotFound(proposal_id)
    proposal = proposals[proposal_id]
    history_entry = {
        "at": now_iso(),
        "action": "revise",
        "old_content": proposal.content,
        "new_content": new_content,
    }
    append_jsonl(
        PROPOSALS_PATH,
        {
            "action": "revise",
            "proposal_id": proposal_id,
            "new_content": new_content,
            "updated_at": now_iso(),
            "history_entry": history_entry,
        },
    )


def get(proposal_id: str) -> MemoryProposal:
    proposals = _rebuild_state()
    if proposal_id not in proposals:
        raise ProposalNotFound(proposal_id)
    return proposals[proposal_id]


def list_proposals(status: Optional[str] = None, limit: Optional[int] = None) -> List[MemoryProposal]:
    proposals = list(_rebuild_state().values())
    if status:
        proposals = [p for p in proposals if p.status == status]
    proposals.sort(key=lambda p: p.created_at)
    if limit:
        proposals = proposals[-limit:]
    return proposals
