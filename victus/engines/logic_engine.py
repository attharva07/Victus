from __future__ import annotations

import os
import re
from typing import Any, Dict
from uuid import uuid4

from core.orchestrator.deterministic import parse_intent
from core.orchestrator.policy import validate_intent
from core.security.bootstrap_store import is_bootstrapped
from victus.contracts.orchestrator_result import OrchestratorResult
from victus.core.intent_router import route_intent


class LogicEngine:
    def run(self, user_text: str, context: dict | None) -> OrchestratorResult:
        text = user_text.strip()
        active_context, context_ready = self._ensure_context(context)
        self._debug_log(
            user_text=text,
            context_keys=sorted(active_context.keys()),
            resolver_path="preflight",
            action="n/a",
            confidence=0.0,
        )

        if not text:
            return self._build_result(
                decision="needs_clarification",
                intent={"action": "clarify", "parameters": {}},
                confidence=0.2,
                policy={"allowed": True, "reason_code": "missing_input"},
                required_inputs=["text"],
            )

        policy = self._policy_gate(text, active_context)
        if not policy["allowed"]:
            return self._build_result(
                decision="deny",
                intent={"action": "blocked", "parameters": {"text": text}},
                confidence=0.95,
                policy=policy,
                required_inputs=[],
            )

        intent, resolver_path = self._classify_intent(text, active_context)
        if not context_ready:
            intent["confidence"] = min(float(intent.get("confidence", 0.0)), 0.75)

        decision = "allow"
        required_inputs: list[str] = []

        if intent["action"] in {"reminder.create", "reminder.create_draft"}:
            missing = self._missing_reminder_inputs(intent.get("parameters", {}))
            if missing:
                decision = "needs_clarification"
                required_inputs = missing
                if intent["action"] == "reminder.create":
                    intent["action"] = "reminder.create_draft"
        elif intent["action"] == "unknown":
            decision = "needs_clarification"
            required_inputs = ["clarification"]

        confidence = float(intent.get("confidence", 0.8))
        self._debug_log(
            user_text=text,
            context_keys=sorted(active_context.keys()),
            resolver_path=resolver_path,
            action=intent["action"],
            confidence=confidence,
        )
        return self._build_result(
            decision=decision,
            intent={"action": intent["action"], "parameters": intent.get("parameters", {})},
            confidence=confidence,
            policy=policy,
            required_inputs=required_inputs,
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

        if "runtime_context" not in active:
            try:
                from victus_local.victus_adapter import _build_context

                active["runtime_context"] = _build_context().model_dump()
            except Exception:
                pass

        return active, context_ready

    def _classify_intent(self, text: str, context: dict[str, Any]) -> tuple[Dict[str, Any], str]:
        reminder = self._reminder_fast_path(text)
        if reminder is not None:
            return reminder, "rules:reminder_fast_path"

        parser = context.get("deterministic_parser") or parse_intent
        parsed = parser(text)
        if parsed is not None:
            validated = validate_intent(parsed)
            return {
                "action": validated.action if validated.action != "noop" else "unknown",
                "parameters": validated.parameters,
                "confidence": validated.confidence,
            }, "classifier:core.orchestrator.deterministic.parse_intent"

        routed = route_intent(text)
        if routed is not None:
            action = "system.status.query" if routed.action == "status" else f"system.{routed.action}"
            return {"action": action, "parameters": routed.args, "confidence": 0.85}, "rules:victus.core.intent_router"

        lowered = text.lower()
        if any(token in lowered for token in ["status", "health", "uptime"]):
            return {"action": "system.status.query", "parameters": {}, "confidence": 0.8}, "fallback:status_keywords"

        return {"action": "unknown", "parameters": {}, "confidence": 0.4}, "fallback:unknown"

    def _reminder_fast_path(self, text: str) -> Dict[str, Any] | None:
        normalized = " ".join(text.strip().split())
        lowered = normalized.lower()
        prefixes = ("add reminder", "set reminder", "remind me")
        matched_prefix = next((prefix for prefix in prefixes if lowered.startswith(prefix)), None)
        if not matched_prefix:
            return None

        remainder = normalized[len(matched_prefix) :].strip(" ,")
        remainder = re.sub(r"^to\s+", "", remainder, flags=re.IGNORECASE)

        date_match = re.search(r"\b(today|tomorrow|next\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday))\b", remainder, flags=re.IGNORECASE)
        time_match = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", remainder, flags=re.IGNORECASE)

        when: Dict[str, str] = {}
        if date_match:
            when["date"] = date_match.group(1).lower()
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or "0")
            meridiem = time_match.group(3).lower()
            if meridiem == "pm" and hour != 12:
                hour += 12
            if meridiem == "am" and hour == 12:
                hour = 0
            when["time"] = f"{hour:02d}:{minute:02d}:00"

        cleanup_tokens = []
        if date_match:
            cleanup_tokens.append(date_match.group(0))
        if time_match:
            cleanup_tokens.append(time_match.group(0))

        title = remainder
        for token in cleanup_tokens:
            title = re.sub(re.escape(token), "", title, flags=re.IGNORECASE)
        title = re.sub(r"\s+", " ", title).strip(" ,-.")

        params: Dict[str, Any] = {"title": title or "reminder"}
        if when:
            params["when"] = when

        if date_match and time_match:
            return {"action": "reminder.create", "parameters": params, "confidence": 0.9}

        return {"action": "reminder.create_draft", "parameters": params, "confidence": 0.84}

    def _missing_reminder_inputs(self, params: Dict[str, Any]) -> list[str]:
        when = params.get("when") if isinstance(params.get("when"), dict) else {}
        missing: list[str] = []
        has_date = bool(when.get("date"))
        has_time = bool(when.get("time"))
        if has_time and not has_date:
            missing.append("date")
        elif has_date and not has_time:
            missing.append("time")
        elif not has_date and not has_time:
            missing.extend(["date", "time"])
        return missing

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
    ) -> OrchestratorResult:
        if not policy.get("allowed", True):
            decision = "deny"
            required_inputs = []
        elif decision == "allow":
            required_inputs = []
        elif decision == "needs_clarification" and not required_inputs:
            required_inputs = ["clarification"]

        action = str(intent.get("action", "unknown"))
        return OrchestratorResult(
            trace_id=str(uuid4()),
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
            tool_results=[],
        )

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
