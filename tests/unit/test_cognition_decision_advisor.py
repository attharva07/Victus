from __future__ import annotations

import pytest

from core.cognition import DecisionAdvisor
from core.orchestrator.policy import evaluate_candidates


@pytest.mark.parametrize(
    ("intent_action", "intent_params", "user_text", "expected_actions"),
    [
        (
            "finance.add_transaction",
            {"amount": 18.5, "category": "food"},
            "add this transaction",
            ["finance.add_transaction", "finance.add_transaction_draft", "finance.add_transaction_confirm"],
        ),
        ("reminder.add", {"title": "study"}, "set a reminder", ["reminder.add"]),
        ("file.delete", {"path": "notes.txt"}, "delete the file", ["file.delete", "file.archive", "file.move_to_trash"]),
        ("unknown.action", {}, "do the thing", ["unknown.action", "clarify"]),
        ("admin.delete_user", {"user_id": "u1"}, "delete this user", ["admin.delete_user"]),
    ],
)
def test_candidate_generation_examples(
    intent_action: str,
    intent_params: dict[str, object],
    user_text: str,
    expected_actions: list[str],
) -> None:
    advisor = DecisionAdvisor()
    plan = advisor.evaluate(
        intent_action=intent_action,
        intent_params=intent_params,
        user_text=user_text,
        context={"intent_confidence": 0.9},
    )
    actions = [candidate.action for candidate in plan.candidates]
    for expected in expected_actions:
        assert expected in actions


def test_scoring_is_deterministic() -> None:
    advisor = DecisionAdvisor()
    kwargs = dict(
        intent_action="finance.add_transaction",
        intent_params={"amount": 42.0, "category": "books"},
        user_text="add a finance transaction for books",
        context={"intent_confidence": 0.88, "exam_week": True},
    )
    plan1 = advisor.evaluate(**kwargs)
    plan2 = advisor.evaluate(**kwargs)

    assert [candidate.action for candidate in plan1.candidates] == [candidate.action for candidate in plan2.candidates]
    for left, right in zip(plan1.candidates, plan2.candidates, strict=True):
        assert left.score_total == pytest.approx(right.score_total, abs=1e-9)
        assert left.score_breakdown == right.score_breakdown


def test_admin_delete_user_is_low_score_and_denied_by_policy() -> None:
    advisor = DecisionAdvisor()
    plan = advisor.evaluate(
        intent_action="admin.delete_user",
        intent_params={"user_id": "abc"},
        user_text="delete user abc",
        context={"intent_confidence": 0.95},
    )
    admin_candidate = next(c for c in plan.candidates if c.action == "admin.delete_user")
    assert admin_candidate.score_breakdown["risk"] <= 0.1

    policy = evaluate_candidates(plan.candidates)
    denied = {decision.action: decision.reason for decision in policy.decisions if not decision.allowed}
    assert denied["admin.delete_user"] == "admin_actions_require_manual_review"


def test_snapshot_like_stable_order_and_scores() -> None:
    advisor = DecisionAdvisor()
    plan = advisor.evaluate(
        intent_action="file.delete",
        intent_params={"path": "report.txt"},
        user_text="delete report",
        context={"intent_confidence": 0.7},
    )

    snapshot = [
        (candidate.action, candidate.score_total, candidate.score_breakdown)
        for candidate in plan.candidates
    ]
    rerun = advisor.evaluate(
        intent_action="file.delete",
        intent_params={"path": "report.txt"},
        user_text="delete report",
        context={"intent_confidence": 0.7},
    )
    rerun_snapshot = [
        (candidate.action, candidate.score_total, candidate.score_breakdown)
        for candidate in rerun.candidates
    ]

    assert [row[0] for row in snapshot] == [row[0] for row in rerun_snapshot]
    for left, right in zip(snapshot, rerun_snapshot, strict=True):
        assert left[1] == pytest.approx(right[1], abs=1e-9)
        assert left[2] == right[2]
