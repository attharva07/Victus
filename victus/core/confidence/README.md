# Victus Confidence Subsystem

The confidence subsystem provides deterministic, namespaced confidence tracking for Victus features.

## Why

- Keep confidence behavior predictable and testable.
- Isolate independent confidence domains (for example, `router.*` versus `ui.*`).
- Persist confidence state and event history for auditability.

## Package layout

- `models.py`: Typed confidence models.
- `events.py`: Event schema helpers and normalization.
- `keys.py`: Namespace-safe key creation and validation.
- `store.py`: JSON-backed persistence at `victus/data/confidence/store.json`.
- `core.py`: Deterministic score update rules.
- `legacy.py`: Existing plan-confidence logic preserved for compatibility.
- `ui.py`: UI confidence scaffold API for layout actions and feedback events.
- Router domain selection now writes deterministic scores under `router.domain.*` keys (for example, `router.domain.finance`, `router.domain.memories`, `router.domain.files`) via `ConfidenceCore` + `ConfidenceStore`.

## How to emit events

```python
from victus.core.confidence import ConfidenceCore, ConfidenceStore, normalize_event

store = ConfidenceStore()
core = ConfidenceCore(store)

event = normalize_event(
    key="router.domain",
    event_type="accept",
    weight=1.0,
    meta={"source": "router"},
)
updated = core.apply_event(event)
print(updated.value)
```

## UI layout confidence scaffold

UI layout confidence uses fixed action keys under `ui.layout.*`:

- `ui.layout.pin_reminders`
- `ui.layout.pin_alerts`
- `ui.layout.freeze_layout`
- `ui.layout.promote_workflow`
- `ui.layout.demote_low_priority`

UI components can report feedback using the scaffold helper:

```python
from victus.core.confidence import get_ui_score, record_ui_event

record_ui_event(
    action_key="ui.layout.pin_alerts",
    event_type="ui.acknowledged_alert",
    meta={"surface": "notification_panel"},
)

score = get_ui_score("ui.layout.pin_alerts")
print(score.value)
```

Feedback strength categories:

- **Strong negative**: explicit user correction or disablement (for example, `ui.user_override_drag_back`, `ui.user_disable_adaptive`).
- **Strong positive**: explicit user endorsement (for example, `ui.user_pin_manual`).
- **Medium negative**: ignored high-signal item (`ui.ignored_urgent_item`).
- **Positive**: clear acknowledgment (`ui.acknowledged_alert`).
- **Weak positive**: passive non-complaint (`ui.no_complaint_timeout`).

> Warning: silence (`ui.no_complaint_timeout`) is intentionally weak feedback. It should never outweigh explicit user correction events.

## Scoring rules

- All scores are clamped to `[0.0, 1.0]`.
- Positive event types (`accept`, `confirm`, `success`) increase scores.
- Negative event types (`reject`, `override`, `failure`, `clarify`) decrease scores with a stronger default step.
- Optional decay toward neutral (`0.5`) exists, but is disabled by default.
