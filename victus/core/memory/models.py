from dataclasses import dataclass, field
from typing import List


ALLOWED_CATEGORIES = {
    "user_preferences",
    "project_state",
    "operational_rules",
    "confirmed_long_term_facts",
}

CONFIDENCE_LEVELS = {"low", "medium", "high"}


@dataclass
class MemoryRecord:
    id: str
    category: str
    content: str
    source: str
    created_at: str
    confidence: str
    tags: List[str] = field(default_factory=list)


@dataclass
class MemoryProposal:
    proposal_id: str
    category: str
    content: str
    confidence: str
    tags: List[str]
    status: str
    created_at: str
    updated_at: str
    history: List[dict] = field(default_factory=list)
