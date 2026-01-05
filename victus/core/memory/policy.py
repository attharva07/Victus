"""Memory write policy enforcement."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, List, Tuple

if TYPE_CHECKING:
    from .proposals import MemoryProposal


MEMORY_TYPES = {
    "preference",
    "project_context",
    "workflow_rule",
    "ephemeral",
    "identity_sensitive",
}


@dataclass
class MemoryPolicy:
    secret_patterns: List[str] = field(default_factory=list)

    @classmethod
    def load(cls, path: Path) -> "MemoryPolicy":
        if not path.exists():
            return cls()
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(secret_patterns=data.get("secret_patterns", []))


def _matches_secret(content: str, patterns: List[str]) -> bool:
    for pattern in patterns:
        if re.search(pattern, content):
            return True
    return False


def validate_memory_write(proposal: "MemoryProposal", policy: MemoryPolicy) -> Tuple[bool, List[str]]:
    reasons: List[str] = []

    if proposal.memory_type not in MEMORY_TYPES:
        reasons.append("memory_type is not allowed")

    if proposal.source != "manual_review":
        reasons.append("memory writes require manual_review source")

    if proposal.memory_type == "ephemeral":
        reasons.append("ephemeral memory cannot be persisted")

    if _matches_secret(proposal.content, policy.secret_patterns):
        reasons.append("content appears to contain secrets")

    if proposal.memory_type == "identity_sensitive" and not proposal.explicit_user_request:
        reasons.append("identity_sensitive memory requires explicit user request")

    return len(reasons) == 0, reasons
