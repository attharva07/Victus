from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class PriorityClassification(str, Enum):
    critical = "critical"
    high = "high"
    normal = "normal"
    low = "low"


class EmailMetadata(BaseModel):
    message_id: str
    thread_id: str
    subject: str
    sender: str
    recipients: list[str] = Field(default_factory=list)
    cc: list[str] = Field(default_factory=list)
    sent_at: datetime
    received_at: datetime
    labels: list[str] = Field(default_factory=list)
    is_unread: bool = False
    has_attachments: bool = False


class NormalizedEmail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metadata: EmailMetadata
    body_text: str
    body_html: str | None = None
    cleaned_text: str
    quoted_history_removed: bool = False
    signature_removed: bool = False


class ActionItem(BaseModel):
    description: str
    owner_hint: str | None = None
    due_at: datetime | None = None
    source_excerpt: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)


class PriorityScore(BaseModel):
    classification: PriorityClassification
    score: float = Field(ge=0.0, le=1.0)
    reasons: list[str] = Field(default_factory=list)


class ThreadSummary(BaseModel):
    thread_id: str
    subject: str
    participant_count: int = Field(ge=0)
    message_count: int = Field(ge=0)
    summary: str
    unresolved_questions: list[str] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)


class DigestResult(BaseModel):
    generated_at: datetime
    unread: list[NormalizedEmail] = Field(default_factory=list)
    important: list[NormalizedEmail] = Field(default_factory=list)
    action_needed: list[ActionItem] = Field(default_factory=list)
    highlights: list[str] = Field(default_factory=list)
