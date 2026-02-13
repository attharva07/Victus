import pytest
from victus.core.confidence import get_router_confidence_store
from victus.core.schemas import Context, PrivacySettings
from victus_local.media_router import build_confidence
from victus_local.victus_adapter import _domain_scores_for_route, _local_rule_router


def _context() -> Context:
    from datetime import datetime, timezone

    return Context(
        session_id="test",
        timestamp=datetime.now(timezone.utc),
        mode="dev",
        foreground_app=None,
        privacy=PrivacySettings(allow_send_to_openai=True),
    )


def test_router_keeps_domain_selection_for_known_inputs():
    context = _context()

    productivity_plan = _local_rule_router("open calculator", context)
    assert productivity_plan is not None
    assert productivity_plan.domain == "productivity"

    system_plan = _local_rule_router("show cpu usage", context)
    assert system_plan is not None
    assert system_plan.domain == "system"


def test_router_domain_confidence_ordering_unchanged():
    system_scores = _domain_scores_for_route("system")
    assert system_scores["system"] > system_scores["productivity"]

    productivity_scores = _domain_scores_for_route("productivity")
    assert productivity_scores["productivity"] > productivity_scores["system"]


def test_router_edge_case_unchanged_for_unroutable_input():
    context = _context()
    assert _local_rule_router("   ", context) is None
    assert _local_rule_router("tell me a joke", context) is None


def test_router_persists_domain_scores_under_router_namespace():
    context = _context()
    _local_rule_router("open calculator", context)

    scores = get_router_confidence_store().get_namespace("router.domain")
    assert "router.domain.productivity" in scores
    assert "router.domain.system" in scores
    assert scores["router.domain.productivity"] == 1.0
    assert scores["router.domain.system"] == 0.0


def test_media_confidence_formula_and_decision_unchanged():
    confidence = build_confidence(
        parse_conf=0.8,
        parse_reasons=["parse ok"],
        retrieval_conf=0.4,
        retrieval_reasons=["retrieval ok"],
    )

    # Existing weighted blend: 0.55 * parse + 0.45 * retrieval.
    assert confidence["final"] == pytest.approx(0.62)
    # Existing decision thresholds are unchanged.
    assert confidence["decision"] == "soft_confirm"
    assert confidence["reasons"] == ["parse ok", "retrieval ok"]
