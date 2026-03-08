from __future__ import annotations

from datetime import datetime, timezone

import pytest

from core.mail_intelligence.connector import MailConnectorConfig, MailConnectorError, RawEmail, ReadOnlyConnectorGuard
from core.mail_intelligence.models import EmailMetadata, PriorityClassification
from core.mail_intelligence.normalization import EmailNormalizer
from core.mail_intelligence.service import MailIntelligenceService


class _FakeConnector:
    def __init__(self, raw_email: RawEmail):
        self._email = raw_email

    def list_unread(self, *, limit: int = 25) -> list[RawEmail]:
        return [self._email][:limit]

    def get_message(self, message_id: str) -> RawEmail:
        return self._email

    def list_thread(self, thread_id: str) -> list[RawEmail]:
        return [self._email]


def _sample_email(body_text: str) -> RawEmail:
    metadata = EmailMetadata(
        message_id="m1",
        thread_id="t1",
        subject="Urgent: launch blocker",
        sender="lead@vendor.com",
        recipients=["you@company.com"],
        cc=[],
        sent_at=datetime.now(tz=timezone.utc),
        received_at=datetime.now(tz=timezone.utc),
        labels=["INBOX", "UNREAD"],
        is_unread=True,
        has_attachments=False,
    )
    return RawEmail(metadata=metadata, body_text=body_text)


def test_normalizer_removes_quoted_and_signature() -> None:
    email = _sample_email(
        "Please review this ASAP.\n\nThanks,\nAlex\n\nOn Tue wrote:\n> old text"
    )
    normalized = EmailNormalizer().normalize(email)

    assert "On Tue wrote" not in normalized.cleaned_text
    assert "Thanks," not in normalized.cleaned_text
    assert normalized.quoted_history_removed is True
    assert normalized.signature_removed is True


def test_service_summarize_email_scores_high_priority() -> None:
    connector = _FakeConnector(_sample_email("Can you ship this today?"))
    guard = ReadOnlyConnectorGuard(
        config=MailConnectorConfig(enabled=True, provider="gmail", has_credentials=True, read_scope_granted=True)
    )
    service = MailIntelligenceService(connector=connector, guard=guard)

    summary, score = service.summarize_email("m1")

    assert "Can you ship this today?" in summary
    assert score.classification in {PriorityClassification.high, PriorityClassification.critical}


def test_guard_fails_closed_when_missing_scope() -> None:
    guard = ReadOnlyConnectorGuard(
        config=MailConnectorConfig(enabled=True, provider="gmail", has_credentials=True, read_scope_granted=False)
    )

    with pytest.raises(MailConnectorError):
        guard.assert_can_read()
