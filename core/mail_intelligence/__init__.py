from core.mail_intelligence.connector import (
    MailConnector,
    MailConnectorConfig,
    MailConnectorError,
    RawEmail,
    ReadOnlyConnectorGuard,
)
from core.mail_intelligence.intelligence import ActionExtractor, RulesPriorityScorer, Summarizer
from core.mail_intelligence.intents import MAIL_INTENTS
from core.mail_intelligence.models import (
    ActionItem,
    DigestResult,
    EmailMetadata,
    NormalizedEmail,
    PriorityClassification,
    PriorityScore,
    ThreadSummary,
)
from core.mail_intelligence.normalization import EmailNormalizer
from core.mail_intelligence.service import MailIntelligenceService

__all__ = [
    "ActionExtractor",
    "ActionItem",
    "DigestResult",
    "EmailMetadata",
    "EmailNormalizer",
    "MAIL_INTENTS",
    "MailConnector",
    "MailConnectorConfig",
    "MailConnectorError",
    "MailIntelligenceService",
    "NormalizedEmail",
    "PriorityClassification",
    "PriorityScore",
    "RawEmail",
    "ReadOnlyConnectorGuard",
    "RulesPriorityScorer",
    "Summarizer",
    "ThreadSummary",
]
