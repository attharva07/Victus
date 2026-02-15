from __future__ import annotations

import json

import pytest

from core.orchestrator.deterministic import _router_confidence_components, parse_intent


@pytest.fixture(autouse=True)
def _isolate_router_confidence_store(monkeypatch: pytest.MonkeyPatch, tmp_path):
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    _router_confidence_components.cache_clear()
    yield
    _router_confidence_components.cache_clear()


@pytest.mark.parametrize(
    "utterance,expected_action",
    [
        ("camera status", "camera.status"),
        ("remember buy milk", "memory.add"),
        ("paid 12 on groceries", "finance.add_transaction"),
        ("list files", "files.list"),
        ("tell me a joke", None),
    ],
)
def test_router_selection_is_unchanged(utterance: str, expected_action: str | None) -> None:
    intent = parse_intent(utterance)
    if expected_action is None:
        assert intent is None
        return
    assert intent is not None
    assert intent.action == expected_action


def test_router_domain_confidence_ordering_unchanged() -> None:
    intent = parse_intent("list files")
    assert intent is not None
    assert intent.action == "files.list"

    store_path = _router_confidence_components()[0].path
    payload = json.loads(store_path.read_text(encoding="utf-8"))
    scores = payload["scores"]

    assert scores["router.domain.files"]["value"] == 1.0
    assert scores["router.domain.camera"]["value"] == 0.0
    assert scores["router.domain.memories"]["value"] == 0.0
    assert scores["router.domain.finance"]["value"] == 0.0


def test_router_edge_case_regression() -> None:
    assert parse_intent("paid groceries") is None
