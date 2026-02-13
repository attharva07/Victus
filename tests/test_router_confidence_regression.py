from victus.core.schemas import Context, PrivacySettings
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
