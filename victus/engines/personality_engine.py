from __future__ import annotations

from typing import Any, Dict, List

from victus.contracts.orchestrator_result import OrchestratorResult
from victus.contracts.rendered_result import RenderedResult


class PersonalityEngine:
    def render(self, orchestrator_result: OrchestratorResult, profile: Dict[str, Any]) -> RenderedResult:
        tone = str(profile.get("tone", "neutral"))
        verbosity = str(profile.get("verbosity", "normal"))
        if verbosity not in {"short", "normal", "detailed"}:
            verbosity = "normal"

        decision = orchestrator_result.decision
        action = str(orchestrator_result.intent.get("action", "unknown"))
        reason_code = orchestrator_result.policy.reason_code

        if decision == "needs_clarification":
            required = ", ".join(orchestrator_result.required_inputs) or "additional details"
            headline = "Need a bit more detail"
            body = f"Please provide: {required}."
            bullets = [f"Missing: {item}" for item in orchestrator_result.required_inputs]
        elif decision == "deny":
            headline = "I can’t complete that request"
            body = f"This request is blocked by policy ({reason_code})."
            bullets = ["Try a safer alternative.", "No action was executed."]
        else:
            headline = f"Ready to proceed: {action}"
            body = f"Policy check passed and confidence is {orchestrator_result.confidence_tier}."
            bullets = [f"Action: {action}", f"Reason: {reason_code}"]

        if verbosity == "short":
            bullets = bullets[:1]
        elif verbosity == "detailed":
            bullets = bullets + [f"Tone: {tone}", f"Trace: {orchestrator_result.trace_id}"]

        if tone == "friendly":
            body = f"Absolutely — {body}"
        elif tone == "formal":
            body = f"Notice: {body}"

        return RenderedResult(
            trace_id=orchestrator_result.trace_id,
            headline=headline,
            body=body,
            bullets=bullets,
            tone_profile=tone,
            verbosity_level=verbosity,
            ui_copy_hints={"decision": decision},
        )
