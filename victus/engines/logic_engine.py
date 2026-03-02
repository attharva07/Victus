from __future__ import annotations

import re
from typing import Any, Dict
from uuid import uuid4

from core.orchestrator.deterministic import parse_intent
from core.orchestrator.policy import validate_intent
from victus.contracts.orchestrator_result import OrchestratorResult


class LogicEngine:
    def run(self, user_text: str, context: dict) -> OrchestratorResult:
        text = user_text.strip()
        if not text:
            return self._build_result(
                decision="needs_clarification",
                intent={"action": "clarify", "parameters": {}},
                confidence=0.2,
                policy={"allowed": True, "reason_code": "missing_input"},
                required_inputs=["text"],
            )

        policy = self._policy_gate(text, context)
        if not policy["allowed"]:
            return self._build_result(
                decision="deny",
                intent={"action": "blocked", "parameters": {"text": text}},
                confidence=0.95,
                policy=policy,
                required_inputs=[],
            )

        intent = self._classify_intent(text)
        if intent["action"] == "productivity.reminder.create":
            missing = self._missing_reminder_inputs(intent["parameters"])
            if missing:
                return self._build_result(
                    decision="needs_clarification",
                    intent=intent,
                    confidence=0.65,
                    policy=policy,
                    required_inputs=missing,
                )

        if intent["action"] == "unknown":
            return self._build_result(
                decision="needs_clarification",
                intent=intent,
                confidence=0.4,
                policy=policy,
                required_inputs=["action"],
            )

        confidence = float(intent.get("confidence", 0.8))
        return self._build_result(
            decision="allow",
            intent={"action": intent["action"], "parameters": intent["parameters"]},
            confidence=confidence,
            policy=policy,
            required_inputs=[],
        )

    def _classify_intent(self, text: str) -> Dict[str, Any]:
        parsed = parse_intent(text)
        if parsed is not None:
            validated = validate_intent(parsed)
            return {
                "action": validated.action if validated.action != "noop" else "unknown",
                "parameters": validated.parameters,
                "confidence": validated.confidence,
            }

        lowered = text.lower()
        reminder_match = re.search(r"remind me to (?P<task>.+?)(?: at (?P<time>.+))?$", lowered)
        if reminder_match:
            params: Dict[str, Any] = {"task": reminder_match.group("task").strip()}
            if reminder_match.group("time"):
                params["time"] = reminder_match.group("time").strip()
            return {"action": "productivity.reminder.create", "parameters": params, "confidence": 0.86}

        if any(token in lowered for token in ["status", "health", "uptime"]):
            return {"action": "system.status.query", "parameters": {}, "confidence": 0.8}

        return {"action": "unknown", "parameters": {}, "confidence": 0.4}

    def _missing_reminder_inputs(self, params: Dict[str, Any]) -> list[str]:
        missing: list[str] = []
        if not params.get("task"):
            missing.append("task")
        if not params.get("time"):
            missing.append("time")
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
