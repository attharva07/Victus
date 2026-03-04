from __future__ import annotations

import hashlib
import json
from typing import Any

from core.cognition.models import CandidateAction, DecisionPlan


class DecisionAdvisor:
    """Heuristic-only advisor. Generates and ranks candidate actions without executing them."""

    _WEIGHTS = {
        "risk": 0.25,
        "effort": 0.15,
        "utility": 0.25,
        "confidence": 0.15,
        "reversibility": 0.10,
        "time": 0.10,
    }

    def evaluate(
        self,
        *,
        intent_action: str,
        intent_params: dict[str, Any],
        user_text: str,
        context: dict[str, Any],
        history_summary: str | None = None,
        system_state: dict[str, Any] | None = None,
    ) -> DecisionPlan:
        trace_id = self._trace_id(
            intent_action=intent_action,
            intent_params=intent_params,
            user_text=user_text,
            context=context,
            history_summary=history_summary,
            system_state=system_state,
        )
        candidates = self._generate_candidates(intent_action, intent_params, user_text)
        scored = [self._score_candidate(c, intent_action, user_text, context) for c in candidates]
        ranked = sorted(scored, key=lambda c: (-c.score_total, c.action, json.dumps(c.parameters, sort_keys=True)))
        notes = [
            "heuristic_scoring_v1",
            "deterministic_given_same_inputs",
            f"candidate_count={len(ranked)}",
        ]
        selected = ranked[0] if ranked else None
        return DecisionPlan(candidates=ranked, selected=selected, notes=notes, trace_id=trace_id)

    def rerank_after_policy(
        self,
        *,
        plan: DecisionPlan,
        allowed_actions: set[str],
        denied_reasons: dict[str, str] | None = None,
    ) -> DecisionPlan:
        denied_reasons = denied_reasons or {}
        allowed = [c for c in plan.candidates if c.action in allowed_actions]
        notes = list(plan.notes)
        if denied_reasons:
            notes.extend(f"policy_denied:{action}:{reason}" for action, reason in sorted(denied_reasons.items()))
        if not allowed:
            notes.append("no_allowed_candidates")
            return DecisionPlan(candidates=[], selected=None, notes=notes, trace_id=plan.trace_id)
        ranked = sorted(allowed, key=lambda c: (-c.score_total, c.action, json.dumps(c.parameters, sort_keys=True)))
        notes.append(f"allowed_count={len(ranked)}")
        return DecisionPlan(candidates=ranked, selected=ranked[0], notes=notes, trace_id=plan.trace_id)

    def _generate_candidates(self, intent_action: str, intent_params: dict[str, Any], user_text: str) -> list[CandidateAction]:
        candidates: list[CandidateAction] = []
        if intent_action and isinstance(intent_params, dict):
            candidates.append(
                CandidateAction(
                    action=intent_action,
                    parameters=dict(intent_params),
                    score_total=0.0,
                    score_breakdown={},
                    rationale="Direct intent match from parser.",
                )
            )

        if intent_action == "finance.add_transaction":
            candidates.append(self._blank("finance.add_transaction_draft", intent_params, "Safer draft-first path."))
            candidates.append(self._blank("finance.add_transaction_confirm", intent_params, "Add explicit confirmation gate."))
        elif intent_action.startswith("file.delete") or intent_action == "file.delete":
            candidates.append(self._blank("file.archive", intent_params, "Prefer reversible archive operation."))
            candidates.append(self._blank("file.move_to_trash", intent_params, "Move to trash before permanent delete."))
        elif intent_action.endswith(".send") or intent_action.startswith("send"):
            candidates.append(self._blank("draft", intent_params, "Create draft before sending."))

        if not candidates or intent_action == "unknown.action":
            clarify_params = {
                "missing": ["target_action", "required_parameters"],
                "question": f"Please clarify requested action for: {user_text.strip()[:80]}",
            }
            candidates.append(self._blank("clarify", clarify_params, "Insufficient or unknown action; request structured clarification."))
        return candidates

    @staticmethod
    def _blank(action: str, params: dict[str, Any], rationale: str) -> CandidateAction:
        return CandidateAction(action=action, parameters=dict(params), score_total=0.0, score_breakdown={}, rationale=rationale)

    def _score_candidate(
        self,
        candidate: CandidateAction,
        intent_action: str,
        user_text: str,
        context: dict[str, Any],
    ) -> CandidateAction:
        risk = self._risk_score(candidate.action)
        effort = self._effort_score(candidate.parameters)
        utility = self._utility_score(candidate.action, intent_action, user_text, context)
        reversibility = self._reversibility_score(candidate.action)
        confidence = self._confidence_score(context)
        time = 1.0 - effort * 0.7
        breakdown = {
            "risk": risk,
            "effort": effort,
            "utility": utility,
            "confidence": confidence,
            "reversibility": reversibility,
            "time": max(0.0, min(1.0, time)),
        }
        total = sum(breakdown[key] * self._WEIGHTS[key] for key in self._WEIGHTS)
        required_permissions = self._required_permissions(candidate.action)
        tags = self._tags(candidate.action)
        return CandidateAction(
            action=candidate.action,
            parameters=candidate.parameters,
            score_total=round(max(0.0, min(1.0, total)), 6),
            score_breakdown={k: round(v, 6) for k, v in breakdown.items()},
            rationale=candidate.rationale[:280],
            required_permissions=required_permissions,
            tags=tags,
        )

    def _risk_score(self, action: str) -> float:
        lowered = action.lower()
        if lowered.startswith("admin."):
            return 0.05
        if "delete" in lowered:
            return 0.1
        if lowered.startswith("finance."):
            return 0.35
        if lowered.startswith("file."):
            return 0.5
        if lowered in {"clarify", "chat.reply", "noop"}:
            return 1.0
        return 0.7

    def _effort_score(self, parameters: dict[str, Any]) -> float:
        complexity = len(parameters)
        return max(0.2, 1.0 - (complexity * 0.15))

    def _utility_score(self, action: str, intent_action: str, user_text: str, context: dict[str, Any]) -> float:
        score = 0.55
        if action == intent_action:
            score += 0.30
        if action.startswith("clarify"):
            score = 0.45 if intent_action != "unknown.action" else 0.8
        lowered = user_text.lower()
        exam_week = bool(context.get("exam_week"))
        if exam_week and any(token in action for token in ("study", "reminder", "memory")):
            score += 0.1
        if "remind" in lowered and action.startswith("reminder."):
            score += 0.1
        return max(0.0, min(1.0, score))

    def _reversibility_score(self, action: str) -> float:
        lowered = action.lower()
        if "delete" in lowered and "trash" not in lowered and "archive" not in lowered:
            return 0.05
        if "archive" in lowered or "trash" in lowered or "draft" in lowered:
            return 0.95
        return 0.7

    def _confidence_score(self, context: dict[str, Any]) -> float:
        raw = context.get("intent_confidence", context.get("confidence", 0.75))
        try:
            value = float(raw)
        except (TypeError, ValueError):
            value = 0.75
        return max(0.0, min(1.0, value))

    def _required_permissions(self, action: str) -> list[str]:
        if action.startswith("finance."):
            return ["finance.write"]
        if action.startswith("admin."):
            return ["admin"]
        if action.startswith("file."):
            return ["files.write"] if "write" in action or "delete" in action else ["files.read"]
        return []

    def _tags(self, action: str) -> list[str]:
        tags: list[str] = []
        if "delete" in action:
            tags.append("destructive")
        if "draft" in action or "clarify" in action:
            tags.append("safe_alternative")
        if action.startswith("admin."):
            tags.append("high_risk")
        return tags

    @staticmethod
    def _trace_id(**payload: Any) -> str:
        serial = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serial.encode("utf-8")).hexdigest()[:16]
