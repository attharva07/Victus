"""Proposal staging for memory writes."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from .policy import MemoryPolicy, validate_memory_write
from .store import MemoryStore


class ProposalNotFound(FileNotFoundError):
    pass


PROPOSAL_DIR = Path("victus/data/memory/proposals")
PROPOSALS_PATH = PROPOSAL_DIR
POLICY_PATH = Path("victus/data/memory/policy.json")
STORE_PATH = Path("victus/data/memory/store.json")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class MemoryProposal:
    proposal_id: str
    ts: str
    domain: str
    memory_type: str
    content: str
    source: str
    explicit_user_request: bool
    risk_flags: List[str] = field(default_factory=list)
    status: str = "pending"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def create(
        cls,
        *,
        domain: str,
        memory_type: str,
        content: str,
        source: str,
        explicit_user_request: bool,
        risk_flags: List[str] | None = None,
    ) -> "MemoryProposal":
        safe_content = (content or "")[:500]
        return cls(
            proposal_id=str(uuid.uuid4()),
            ts=_now(),
            domain=domain,
            memory_type=memory_type,
            content=safe_content,
            source=source,
            explicit_user_request=explicit_user_request,
            risk_flags=risk_flags or [],
        )


def save_proposal(proposal: MemoryProposal, directory: Path | None = None) -> Path:
    dir_path = directory or PROPOSALS_PATH
    dir_path.mkdir(parents=True, exist_ok=True)
    path = dir_path / f"{proposal.proposal_id}.json"
    path.write_text(json.dumps(proposal.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _load_proposal(path: Path) -> MemoryProposal:
    data = json.loads(path.read_text(encoding="utf-8"))
    return MemoryProposal(**data)


def list_proposals(directory: Path | None = None) -> List[MemoryProposal]:
    dir_path = directory or PROPOSALS_PATH
    if not dir_path.exists():
        return []
    proposals = [_load_proposal(path) for path in dir_path.glob("*.json")]
    proposals.sort(key=lambda p: p.ts)
    return proposals


def approve_proposal(proposal_id: str, directory: Path | None = None) -> str:
    dir_path = directory or PROPOSALS_PATH
    path = dir_path / f"{proposal_id}.json"
    if not path.exists():
        raise ProposalNotFound(proposal_id)

    proposal = _load_proposal(path)
    if proposal.status != "pending":
        raise PermissionError("Proposal is not pending")
    policy = MemoryPolicy.load(POLICY_PATH)
    allowed, reasons = validate_memory_write(proposal, policy)
    if not allowed:
        raise PermissionError("; ".join(reasons))

    memory_id = str(uuid.uuid4())
    store = MemoryStore(STORE_PATH)
    store.add(
        {
            "id": memory_id,
            "ts": _now(),
            "domain": proposal.domain,
            "memory_type": proposal.memory_type,
            "content": proposal.content,
            "source": proposal.source,
            "explicit_user_request": proposal.explicit_user_request,
            "risk_flags": proposal.risk_flags,
        }
    )

    proposal.status = "approved"
    save_proposal(proposal, dir_path)
    return memory_id
