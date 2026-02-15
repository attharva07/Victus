"""Helpers for generating namespaced confidence keys."""

from __future__ import annotations

_VALID_NAMESPACES = {"router", "ui"}

UI_LAYOUT_PIN_REMINDERS = "ui.layout.pin_reminders"
UI_LAYOUT_PIN_ALERTS = "ui.layout.pin_alerts"
UI_LAYOUT_FREEZE_LAYOUT = "ui.layout.freeze_layout"
UI_LAYOUT_PROMOTE_WORKFLOW = "ui.layout.promote_workflow"
UI_LAYOUT_DEMOTE_LOW_PRIORITY = "ui.layout.demote_low_priority"

UI_LAYOUT_ACTION_KEYS = {
    UI_LAYOUT_PIN_REMINDERS,
    UI_LAYOUT_PIN_ALERTS,
    UI_LAYOUT_FREEZE_LAYOUT,
    UI_LAYOUT_PROMOTE_WORKFLOW,
    UI_LAYOUT_DEMOTE_LOW_PRIORITY,
}


def make_key(namespace: str, *parts: str) -> str:
    """Create a confidence key in `<namespace>.<part>...` format."""

    if namespace not in _VALID_NAMESPACES:
        raise ValueError(f"Unsupported confidence namespace: {namespace}")
    cleaned_parts = [part.strip() for part in parts if part and part.strip()]
    if not cleaned_parts:
        raise ValueError("At least one key segment is required")
    return ".".join([namespace, *cleaned_parts])


def validate_key(key: str) -> None:
    """Validate that a confidence key uses a known namespace."""

    namespace, _, remainder = key.partition(".")
    if namespace not in _VALID_NAMESPACES or not remainder:
        raise ValueError(
            "Confidence keys must be namespaced and start with 'router.' or 'ui.'",
        )


def validate_ui_layout_action_key(action_key: str, *, allow_arbitrary: bool = False) -> None:
    """Validate UI layout action keys against the known scaffold allowlist."""

    validate_key(action_key)
    if action_key in UI_LAYOUT_ACTION_KEYS:
        return
    if allow_arbitrary and action_key.startswith("ui.layout."):
        return
    raise ValueError(
        "Unsupported UI layout action key. Use a key from UI_LAYOUT_ACTION_KEYS or set allow_arbitrary=True.",
    )
