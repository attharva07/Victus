"""UI-facing confidence helpers for layout scaffold event reporting."""

from __future__ import annotations

from typing import Any

from .core import ConfidenceCore
from .events import UIFeedbackEventType, normalize_event, ui_feedback_to_confidence
from .keys import validate_ui_layout_action_key
from .models import ConfidenceScore
from .store import ConfidenceStore


def record_ui_event(
    action_key: str,
    event_type: UIFeedbackEventType,
    meta: dict[str, Any] | None = None,
    *,
    core: ConfidenceCore | None = None,
    allow_arbitrary_keys: bool = False,
) -> ConfidenceScore:
    """Record a UI event and return the updated confidence score for the action key."""

    validate_ui_layout_action_key(action_key, allow_arbitrary=allow_arbitrary_keys)
    confidence_event_type, weight = ui_feedback_to_confidence(event_type)
    event = normalize_event(
        key=action_key,
        event_type=confidence_event_type,
        weight=weight,
        meta=meta or {},
    )
    return _resolve_core(core).apply_event(event)


def get_ui_score(
    action_key: str,
    *,
    core: ConfidenceCore | None = None,
    allow_arbitrary_keys: bool = False,
) -> ConfidenceScore:
    """Get the current UI confidence score for an action key."""

    validate_ui_layout_action_key(action_key, allow_arbitrary=allow_arbitrary_keys)
    return _resolve_core(core).get_score(action_key)


def _resolve_core(core: ConfidenceCore | None) -> ConfidenceCore:
    if core is not None:
        return core
    return ConfidenceCore(ConfidenceStore())
