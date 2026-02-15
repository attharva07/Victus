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

## Scoring rules

- All scores are clamped to `[0.0, 1.0]`.
- Positive event types (`accept`, `confirm`, `success`) increase scores.
- Negative event types (`reject`, `override`, `failure`, `clarify`) decrease scores with a stronger default step.
- Optional decay toward neutral (`0.5`) exists, but is disabled by default.
