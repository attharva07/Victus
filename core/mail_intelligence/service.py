from __future__ import annotations

from core.logging.audit import audit_event, text_hash
from core.mail_intelligence.connector import MailConnector, ReadOnlyConnectorGuard
from core.mail_intelligence.intelligence import ActionExtractor, RulesPriorityScorer, Summarizer, utcnow
from core.mail_intelligence.models import DigestResult, NormalizedEmail, PriorityScore, ThreadSummary
from core.mail_intelligence.normalization import EmailNormalizer


class MailIntelligenceService:
    """Read-only mail intelligence boundary (connector vs intelligence layers)."""

    def __init__(
        self,
        *,
        connector: MailConnector,
        guard: ReadOnlyConnectorGuard,
        normalizer: EmailNormalizer | None = None,
        summarizer: Summarizer | None = None,
        priority_scorer: RulesPriorityScorer | None = None,
        action_extractor: ActionExtractor | None = None,
    ) -> None:
        self._connector = connector
        self._guard = guard
        self._normalizer = normalizer or EmailNormalizer()
        self._summarizer = summarizer or Summarizer()
        self._priority_scorer = priority_scorer or RulesPriorityScorer()
        self._action_extractor = action_extractor or ActionExtractor()

    def list_unread(self, *, limit: int = 25) -> list[NormalizedEmail]:
        self._guard.assert_can_read()
        unread = [self._normalizer.normalize(item) for item in self._connector.list_unread(limit=limit)]
        audit_event("mail_list_unread", count=len(unread))
        return unread

    def summarize_email(self, message_id: str) -> tuple[str, PriorityScore]:
        self._guard.assert_can_read()
        raw_email = self._connector.get_message(message_id)
        email = self._normalizer.normalize(raw_email)
        summary = self._summarizer.summarize_email(email)
        priority = self._priority_scorer.score(email)
        audit_event("mail_summarize_email", message_hash=text_hash(message_id), priority=priority.classification)
        return summary, priority

    def summarize_thread(self, thread_id: str) -> ThreadSummary:
        self._guard.assert_can_read()
        emails = [self._normalizer.normalize(item) for item in self._connector.list_thread(thread_id)]
        action_items = []
        for email in emails:
            action_items.extend(self._action_extractor.extract(email))
        summary = self._summarizer.summarize_thread(emails, action_items)
        audit_event("mail_summarize_thread", thread_hash=text_hash(thread_id), messages=len(emails))
        return summary

    def extract_actions(self, message_id: str) -> list[dict[str, object]]:
        self._guard.assert_can_read()
        email = self._normalizer.normalize(self._connector.get_message(message_id))
        actions = self._action_extractor.extract(email)
        audit_event("mail_extract_actions", message_hash=text_hash(message_id), count=len(actions))
        return [item.model_dump() for item in actions]

    def get_digest(self, *, limit: int = 25) -> DigestResult:
        unread = self.list_unread(limit=limit)
        important: list[NormalizedEmail] = []
        action_needed = []
        highlights: list[str] = []

        for email in unread:
            score = self._priority_scorer.score(email)
            if score.score >= 0.65:
                important.append(email)
            extracted = self._action_extractor.extract(email)
            action_needed.extend(extracted)
            if extracted:
                highlights.append(f"{email.metadata.subject}: {len(extracted)} action item(s)")

        return DigestResult(
            generated_at=utcnow(),
            unread=unread,
            important=important,
            action_needed=action_needed,
            highlights=highlights,
        )
