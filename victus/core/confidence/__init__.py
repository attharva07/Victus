"""Victus confidence subsystem package.

This package exposes:
- Legacy plan-confidence classes used by existing router/app flows.
- New namespaced confidence scoring core + persistence for cross-system confidence.
"""

from .core import ConfidenceCore
from .events import (
    NEGATIVE_EVENT_TYPES,
    POSITIVE_EVENT_TYPES,
    UI_FEEDBACK_EVENT_SPECS,
    UIFeedbackEventType,
    normalize_event,
    ui_feedback_to_confidence,
)
from .keys import UI_LAYOUT_ACTION_KEYS, make_key, validate_key, validate_ui_layout_action_key
from .legacy import (  # Backward-compatible exports.
    ConfidenceEngine,
    ConfidenceEvaluation,
    ConfidenceLogger,
    ConfidencePlanEvaluation,
    IntentSpec,
    ParsedIntent,
)
from .models import ConfidenceEvent, ConfidenceEventType, ConfidenceScore
from .store import ConfidenceStore
from .ui import get_ui_score, record_ui_event

__all__ = [
    "ConfidenceCore",
    "ConfidenceEngine",
    "ConfidenceEvaluation",
    "ConfidenceEvent",
    "ConfidenceEventType",
    "ConfidenceLogger",
    "ConfidencePlanEvaluation",
    "ConfidenceScore",
    "ConfidenceStore",
    "IntentSpec",
    "NEGATIVE_EVENT_TYPES",
    "UIFeedbackEventType",
    "UI_FEEDBACK_EVENT_SPECS",
    "POSITIVE_EVENT_TYPES",
    "ParsedIntent",
    "UI_LAYOUT_ACTION_KEYS",
    "get_ui_score",
    "make_key",
    "normalize_event",
    "record_ui_event",
    "ui_feedback_to_confidence",
    "validate_key",
    "validate_ui_layout_action_key",
]
