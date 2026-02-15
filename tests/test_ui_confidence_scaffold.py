from __future__ import annotations

from datetime import datetime, timezone

import pytest

from victus.core.confidence import (
    ConfidenceCore,
    ConfidenceStore,
    get_ui_score,
    record_ui_event,
)


def test_ui_events_do_not_change_router_scores(tmp_path):
    core = ConfidenceCore(ConfidenceStore(tmp_path / "confidence.json"))

    router_before = core.get_score("router.domain").value
    record_ui_event(
        "ui.layout.pin_reminders",
        "ui.user_pin_manual",
        {"source": "ui"},
        core=core,
    )
    router_after = core.get_score("router.domain").value

    assert router_before == router_after == 0.5


def test_strong_negative_drops_more_than_weak_positive_rises(tmp_path):
    core = ConfidenceCore(ConfidenceStore(tmp_path / "confidence.json"))

    start = get_ui_score("ui.layout.freeze_layout", core=core).value
    after_weak_positive = record_ui_event(
        "ui.layout.freeze_layout",
        "ui.no_complaint_timeout",
        core=core,
    ).value
    after_strong_negative = record_ui_event(
        "ui.layout.freeze_layout",
        "ui.user_override_drag_back",
        core=core,
    ).value

    weak_increase = after_weak_positive - start
    strong_drop = after_weak_positive - after_strong_negative

    assert strong_drop > weak_increase


def test_event_recording_updates_samples_and_timestamp(tmp_path):
    core = ConfidenceCore(ConfidenceStore(tmp_path / "confidence.json"))

    before = get_ui_score("ui.layout.pin_alerts", core=core)
    assert before.samples == 0

    updated = record_ui_event(
        "ui.layout.pin_alerts",
        "ui.acknowledged_alert",
        {"item_id": "alert-1"},
        core=core,
    )

    assert updated.samples == 1
    assert updated.updated_at >= before.updated_at


def test_action_key_validation_blocks_unknown_keys_by_default(tmp_path):
    core = ConfidenceCore(ConfidenceStore(tmp_path / "confidence.json"))

    with pytest.raises(ValueError):
        record_ui_event(
            "ui.layout.random_experiment",
            "ui.acknowledged_alert",
            core=core,
        )


def test_action_key_validation_can_allow_explicit_arbitrary_layout_keys(tmp_path):
    core = ConfidenceCore(ConfidenceStore(tmp_path / "confidence.json"))

    score = record_ui_event(
        "ui.layout.random_experiment",
        "ui.acknowledged_alert",
        core=core,
        allow_arbitrary_keys=True,
    )

    assert score.samples == 1
    assert score.updated_at <= datetime.now(timezone.utc)
