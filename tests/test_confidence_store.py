from __future__ import annotations

from victus.core.confidence import ConfidenceStore, normalize_event


def test_store_round_trip_persists_score_and_events(tmp_path):
    path = tmp_path / "confidence_store.json"
    store = ConfidenceStore(path)

    initial = store.get_score("router.domain")
    assert initial.value == 0.5
    assert initial.samples == 0

    updated = store.update_score("router.domain", 0.77)
    store.append_event(normalize_event("router.domain", "accept", weight=1.0))

    reloaded = ConfidenceStore(path)
    reloaded_score = reloaded.get_score("router.domain")

    assert updated.value == 0.77
    assert reloaded_score.value == 0.77
    assert reloaded_score.samples == 1

    payload = reloaded.load()
    assert len(payload["events"]) == 1
    assert payload["events"][0]["key"] == "router.domain"
