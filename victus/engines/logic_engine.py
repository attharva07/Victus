from __future__ import annotations

import os
import re
import time
from typing import Any, Dict

from core.observability.trace import ensure_trace_id
from core.orchestrator.deterministic import parse_intent
from core.orchestrator.policy import validate_intent
from core.security.bootstrap_store import is_bootstrapped
from victus.contracts.orchestrator_result import OrchestratorResult
from victus.core.intent_router import route_intent
from victus.engines.action_registry import ActionRegistry


class LogicEngine:
    def run(
        self,
        user_text: str,
        context: dict | None,
        *,
        explicit_action: str | None = None,
        explicit_parameters: dict[str, Any] | None = None,
        explicit_source: str | None = None,
    ) -> OrchestratorResult:
        started = time.perf_counter()
        text = user_text.strip()
        active_context, context_ready = self._ensure_context(context)
        trace_id = ensure_trace_id(str(active_context.get("trace_id", "")).strip() or None)
        tracer = active_context.get("tracer")
        stage_timings: dict[str, float] = {}

        if tracer is not None:
            tracer.record_stage("request_parsed", stage_output={"text": text, "explicit_action": explicit_action})

        self._debug_log(user_text=text, context_keys=sorted(active_context.keys()), resolver_path="preflight", action="n/a", confidence=0.0)

        if not text and not explicit_action:
            return self._build_result(
                decision="needs_clarification",
                intent={"action": "clarify", "parameters": {}},
                confidence=0.2,
                policy={"allowed": True, "reason_code": "missing_input"},
                required_inputs=["action"],
                trace_id=trace_id,
                debug={"resolved_action_source": "none", "stage_timings_ms": stage_timings},
            )

        policy = self._policy_gate(text, active_context)
        if tracer is not None:
            tracer.record_stage("policy_checked", stage_input={"text": text}, stage_output=policy)
        if not policy["allowed"]:
            return self._build_result(
                decision="deny",
                intent={"action": "blocked", "parameters": {"text": text}},
                confidence=0.95,
                policy=policy,
                required_inputs=[],
                trace_id=trace_id,
                debug={"resolved_action_source": explicit_source or "heuristic", "stage_timings_ms": stage_timings},
            )

        t0 = time.perf_counter()
        intent, resolver_path = self._resolve_intent(text, explicit_action, explicit_parameters, explicit_source, active_context)
        stage_timings["action_resolved"] = round((time.perf_counter() - t0) * 1000, 3)
        if tracer is not None:
            tracer.record_stage("action_resolved", stage_output={"intent": intent, "resolver_path": resolver_path})

        if not context_ready:
            intent["confidence"] = min(float(intent.get("confidence", 0.0)), 0.75)

        decision = "allow"
        required_inputs: list[str] = []
        reason_code = "allowed"
        tool_results: list[dict[str, Any]] = []

        action = str(intent.get("action", "unknown"))
        spec = ActionRegistry.get(action) if action != "unknown" else None

        if action == "unknown":
            decision = "needs_clarification"
            required_inputs = ["action"]
            reason_code = "missing_action"
        elif spec is None:
            decision = "needs_clarification"
            required_inputs = ["action"]
            reason_code = "unknown_action"
        else:
            missing_inputs = [field for field in spec.required_inputs if intent.get("parameters", {}).get(field) in (None, "")]
            if missing_inputs:
                decision = "needs_clarification"
                required_inputs = missing_inputs
                reason_code = "missing_required_inputs"
            else:
                t1 = time.perf_counter()
                result_payload = spec.executor(intent.get("parameters", {}))
                stage_timings["tool_executed"] = round((time.perf_counter() - t1) * 1000, 3)
                tool_results = [{"action": action, "result": result_payload}]
                if tracer is not None:
                    tracer.record_stage("tool_executed", stage_output={"action": action, "ok": True})

        confidence = float(intent.get("confidence", 0.8))
        stage_timings["total"] = round((time.perf_counter() - started) * 1000, 3)
        if tracer is not None:
            tracer.record_stage("rendered", stage_output={"decision": decision, "reason_code": reason_code})
        self._debug_log(
            user_text=text,
            context_keys=sorted(active_context.keys()),
            resolver_path=resolver_path,
            action=action,
            confidence=confidence,
        )
        return self._build_result(
            decision=decision,
            intent={"action": action, "parameters": intent.get("parameters", {})},
            confidence=confidence,
            policy={"allowed": True, "reason_code": reason_code},
            required_inputs=required_inputs,
            trace_id=trace_id,
            tool_results=tool_results,
            debug={
                "resolved_action_source": resolver_path,
                "list_actions_count": len(ActionRegistry.list_actions()),
                "stage_timings_ms": stage_timings,
            },
        )

    def _ensure_context(self, context: dict | None) -> tuple[dict[str, Any], bool]:
        active: dict[str, Any] = dict(context or {})
        context_ready = True

        if "router" not in active:
            active["router"] = route_intent
        if "deterministic_parser" not in active:
            active["deterministic_parser"] = parse_intent
        if "bootstrapped" not in active:
            try:
                active["bootstrapped"] = is_bootstrapped()
            except Exception:
                context_ready = False
                active["bootstrapped"] = False
        return active, context_ready

    def _resolve_intent(
        self,
        text: str,
        explicit_action: str | None,
        explicit_parameters: dict[str, Any] | None,
        explicit_source: str | None,
        context: dict[str, Any],
    ) -> tuple[Dict[str, Any], str]:
        if explicit_action:
            return {
                "action": explicit_action,
                "parameters": dict(explicit_parameters or {}),
                "confidence": 1.0,
            }, explicit_source or "explicit_top_level"

        heuristic_intent = self._heuristic_classify(text)
        if heuristic_intent is not None:
            return heuristic_intent, "heuristic"

        if os.getenv("VICTUS_ENABLE_LLM_CLASSIFIER") == "1":
            parser = context.get("deterministic_parser") or parse_intent
            parsed = parser(text)
            if parsed is not None:
                validated = validate_intent(parsed)
                return {
                    "action": validated.action if validated.action != "noop" else "unknown",
                    "parameters": validated.parameters,
                    "confidence": validated.confidence,
                }, "llm"

        return {"action": "unknown", "parameters": {}, "confidence": 0.4}, "none"

    def _heuristic_classify(self, text: str) -> Dict[str, Any] | None:
        lowered = text.lower()

        amount_match = re.search(r"\$\s*(\d+(?:\.\d{1,2})?)", lowered)
        if ("spent" in lowered or "bought" in lowered or "transaction" in lowered) and amount_match:
            amount = float(amount_match.group(1))
            merchant = "starbucks" if "starbucks" in lowered else None
            return {
                "action": "finance.add_transaction",
                "parameters": {"amount": amount, "merchant": merchant, "category": "uncategorized"},
                "confidence": 0.78,
                "reason": "heuristic",
            }

        if any(token in lowered for token in ("remind", "tomorrow", " at ", "pm", "am")):
            return {
                "action": "reminder.add",
                "parameters": {"title": text.strip() or "reminder"},
                "confidence": 0.72,
                "reason": "heuristic",
            }

        if "remember" in lowered or "find memory" in lowered or "memory" in lowered:
            return {
                "action": "memory.search",
                "parameters": {"query": text.strip()},
                "confidence": 0.7,
                "reason": "heuristic",
            }
        return None

    def _policy_gate(self, text: str, _context: dict) -> Dict[str, Any]:
        lowered = text.lower()
        if any(term in lowered for term in ["delete system32", "drop database", "exfiltrate", "bypass auth"]):
            return {"allowed": False, "reason_code": "unsafe_action"}
        if any(term in lowered for term in ["reset all users", "grant admin", "root access"]):
            return {"allowed": False, "reason_code": "admin_required"}
        return {"allowed": True, "reason_code": "allowed"}

    def _confidence_tier(self, confidence: float) -> str:
        if confidence < 0.5:
            return "low"
        if confidence < 0.8:
            return "medium"
        return "high"

    def _primary_cards(self, action: str) -> list[str]:
        if action.startswith("memory."):
            return ["memory"]
        if action.startswith("finance."):
            return ["finance"]
        if "reminder" in action:
            return ["reminders"]
        if "status" in action:
            return ["system"]
        return ["general"]

    def _build_result(
        self,
        *,
        decision: str,
        intent: Dict[str, Any],
        confidence: float,
        policy: Dict[str, Any],
        required_inputs: list[str],
        trace_id: str,
        tool_results: list[dict[str, Any]] | None = None,
        debug: dict[str, Any] | None = None,
    ) -> OrchestratorResult:
        if not policy.get("allowed", True):
            decision = "deny"
            required_inputs = []
        elif decision == "allow":
            required_inputs = []

        action = str(intent.get("action", "unknown"))
        result = OrchestratorResult(
            trace_id=trace_id,
            decision=decision,
            intent={"action": action, "parameters": intent.get("parameters", {})},
            confidence=confidence,
            confidence_tier=self._confidence_tier(confidence),
            policy=policy,
            required_inputs=required_inputs,
            ui_hints={
                "primary_cards": self._primary_cards(action),
                "locks": ["policy"] if decision == "deny" else [],
                "safe_fields": ["action", "parameters", "confidence", "reason_code"],
                "redactions": ["sensitive_terms"] if decision == "deny" else [],
            },
            tool_results=tool_results or [],
        )
        if debug is not None:
            result.ui_hints.safe_fields.append("debug")
        return result

    def _debug_log(self, *, user_text: str, context_keys: list[str], resolver_path: str, action: str, confidence: float) -> None:
        if os.getenv("LOGIC_DEBUG") != "1":
            return
        print(
            "[LogicEngine] "
            f"user_text={user_text!r} "
            f"context_keys={context_keys} "
            f"resolver={resolver_path} "
            f"action={action} confidence={confidence:.2f}"
        )
