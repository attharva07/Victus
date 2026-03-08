from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from core.mail_intelligence.models import EmailMetadata


class MailConnectorError(RuntimeError):
    """Raised when the connector cannot satisfy a read operation safely."""


@dataclass(frozen=True)
class RawEmail:
    metadata: EmailMetadata
    body_text: str
    body_html: str | None = None


class MailConnector(Protocol):
    def list_unread(self, *, limit: int = 25) -> list[RawEmail]: ...

    def get_message(self, message_id: str) -> RawEmail: ...

    def list_thread(self, thread_id: str) -> list[RawEmail]: ...


@dataclass(frozen=True)
class MailConnectorConfig:
    enabled: bool
    provider: str
    has_credentials: bool
    read_scope_granted: bool


class ReadOnlyConnectorGuard:
    """Fail-closed connector gate that enforces config/permission preconditions."""

    def __init__(self, config: MailConnectorConfig) -> None:
        self._config = config

    def assert_can_read(self) -> None:
        if not self._config.enabled:
            raise MailConnectorError("mail connector disabled")
        if not self._config.has_credentials:
            raise MailConnectorError("mail connector credentials are missing")
        if not self._config.read_scope_granted:
            raise MailConnectorError("mail read scope not granted")

        if self._config.provider.strip().lower() in {"", "unknown"}:
            raise MailConnectorError("mail provider not configured")
