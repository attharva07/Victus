from __future__ import annotations

from victus.core.confidence import ConfidenceCore, ConfidenceStore, normalize_event


def test_positive_event_increases_score(tmp_path):
    store = ConfidenceStore(tmp_path / "confidence.json")
    core = ConfidenceCore(store)

    before = core.get_score("router.domain").value
    after = core.apply_event(normalize_event("router.domain", "accept", weight=1.0)).value

    assert after > before


def test_negative_event_decreases_more_than_positive_increase(tmp_path):
    store = ConfidenceStore(tmp_path / "confidence.json")
    core = ConfidenceCore(store)

    start = core.get_score("router.domain").value
    after_positive = core.apply_event(normalize_event("router.domain", "accept", weight=1.0)).value
    after_negative = core.apply_event(normalize_event("router.domain", "reject", weight=1.0)).value

    assert (after_positive - start) < (after_positive - after_negative)


def test_clamp_behavior(tmp_path):
    store = ConfidenceStore(tmp_path / "confidence.json")
    core = ConfidenceCore(store)

    high = core.apply_event(normalize_event("router.domain", "accept", weight=100.0)).value
    low = core.apply_event(normalize_event("router.domain", "reject", weight=100.0)).value

    assert high == 1.0
    assert low == 0.0


def test_namespace_isolation_between_router_and_ui(tmp_path):
    store = ConfidenceStore(tmp_path / "confidence.json")
    core = ConfidenceCore(store)

    ui_before = core.get_score("ui.layout.pin_reminders").value
    core.apply_event(normalize_event("router.domain", "accept", weight=1.0))
    ui_after = core.get_score("ui.layout.pin_reminders").value

    assert ui_before == ui_after == 0.5
