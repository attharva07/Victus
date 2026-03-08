from __future__ import annotations

import re
from datetime import datetime, timezone

from core.mail_intelligence.models import (
    ActionItem,
    NormalizedEmail,
    PriorityClassification,
    PriorityScore,
    ThreadSummary,
)


class RulesPriorityScorer:
    """Rules-first scoring. Future cognition/ML can be layered on top."""

    _HIGH_PRIORITY_TERMS = ("urgent", "asap", "blocking", "outage", "sev1", "p1")
    _ACTION_TERMS = ("please", "can you", "need you", "action", "follow up")

    def score(self, email: NormalizedEmail) -> PriorityScore:
        text = f"{email.metadata.subject}\n{email.cleaned_text}".lower()
        score = 0.2
        reasons: list[str] = []

        if email.metadata.is_unread:
            score += 0.2
            reasons.append("unread")
        if any(term in text for term in self._HIGH_PRIORITY_TERMS):
            score += 0.4
            reasons.append("urgent_keywords")
        if "@" in email.metadata.sender and not email.metadata.sender.endswith("@example.local"):
            score += 0.1
            reasons.append("external_sender")
        if any(term in text for term in self._ACTION_TERMS):
            score += 0.2
            reasons.append("action_language")

        score = min(score, 1.0)
        if score >= 0.85:
            classification = PriorityClassification.critical
        elif score >= 0.65:
            classification = PriorityClassification.high
        elif score >= 0.35:
            classification = PriorityClassification.normal
        else:
            classification = PriorityClassification.low
        return PriorityScore(classification=classification, score=score, reasons=reasons)


class ActionExtractor:
    _ACTION_RE = re.compile(r"(?:please|can you|need you to)\s+(.+?)(?:\.|$)", flags=re.IGNORECASE)

    def extract(self, email: NormalizedEmail) -> list[ActionItem]:
        items: list[ActionItem] = []
        for match in self._ACTION_RE.finditer(email.cleaned_text):
            description = match.group(1).strip()
            if not description:
                continue
            items.append(
                ActionItem(
                    description=description,
                    owner_hint=None,
                    due_at=None,
                    source_excerpt=match.group(0)[:180],
                    confidence=0.65,
                )
            )
        return items


class Summarizer:
    def summarize_email(self, email: NormalizedEmail) -> str:
        first_lines = [line for line in email.cleaned_text.split("\n") if line.strip()][:3]
        if not first_lines:
            return "No readable email body was found after normalization."
        return " ".join(first_lines)

    def summarize_thread(self, emails: list[NormalizedEmail], action_items: list[ActionItem]) -> ThreadSummary:
        if not emails:
            return ThreadSummary(
                thread_id="unknown",
                subject="(empty thread)",
                participant_count=0,
                message_count=0,
                summary="No messages available.",
                unresolved_questions=[],
                action_items=[],
            )

        participants = {email.metadata.sender for email in emails}
        snippet = [self.summarize_email(email) for email in emails[:3]]
        return ThreadSummary(
            thread_id=emails[0].metadata.thread_id,
            subject=emails[0].metadata.subject,
            participant_count=len(participants),
            message_count=len(emails),
            summary=" ".join(snippet),
            unresolved_questions=[],
            action_items=action_items,
        )


def utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)
