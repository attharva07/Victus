from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import ValidationError

from core.logging.audit import audit_event
from core.logging.sanitizer import sanitize_payload
from core.orchestrator.contracts import (
    ActionIntent,
    AuditEvent,
    ExecutionError,
    ExecutionResult,
    PolicyDecision,
    RequestEnvelope,
    ToneHints,
    UIHints,
)
from core.orchestrator.policy_gate import evaluate_action
from core.registry.action_registry import ACTION_REGISTRY


class OrchestratorService:
    """Policy-first execution shell. No planning, no inference, fail-closed."""

    def execute(self, payload: dict[str, Any]) -> ExecutionResult:
        request_id = str(payload.get("request_id") or uuid4())
        correlation_id = payload.get("correlation_id")

        try:
            envelope = RequestEnvelope.model_validate({**payload, "request_id": request_id})
        except ValidationError as exc:
            return self._error_result(
                request_id=request_id,
                correlation_id=correlation_id,
                code="INVALID_REQUEST",
                message="Malformed request envelope.",
                details={"errors": exc.errors()},
            )

        if not isinstance(envelope.intent.context, dict):
            return self._error_result(
                request_id=request_id,
                correlation_id=envelope.correlation_id,
                code="INVALID_CONTEXT",
                message="Context must be an object.",
            )

        handler = ACTION_REGISTRY.get(envelope.intent.action)
        if envelope.intent.action not in ACTION_REGISTRY:
            return self._error_result(
                request_id=request_id,
                correlation_id=envelope.correlation_id,
                code="UNKNOWN_ACTION",
                message=f"Action '{envelope.intent.action}' is not registered.",
            )
        if handler is None:
            return self._error_result(
                request_id=request_id,
                correlation_id=envelope.correlation_id,
                code="MISSING_HANDLER",
                message=f"Action '{envelope.intent.action}' has no configured handler.",
            )

        decision = evaluate_action(envelope.intent)
        if not decision.allowed:
            return self._error_result(
                request_id=request_id,
                correlation_id=envelope.correlation_id,
                code="POLICY_DENIED",
                message=f"Policy denied action '{envelope.intent.action}'.",
                details={"reason": decision.reason},
            )

        started_at = datetime.now(tz=timezone.utc)
        sanitized_params = sanitize_payload(envelope.intent.parameters)
        self._emit_audit(
            AuditEvent(
                request_id=request_id,
                correlation_id=envelope.correlation_id,
                action=envelope.intent.action,
                sanitized_parameters=sanitized_params,
                status="started",
                started_at=started_at,
            )
        )

        try:
            outcome = handler(envelope.intent.parameters, envelope.intent.context)
        except Exception as exc:  # noqa: BLE001
            self._emit_audit(
                AuditEvent(
                    request_id=request_id,
                    correlation_id=envelope.correlation_id,
                    action=envelope.intent.action,
                    sanitized_parameters=sanitized_params,
                    status="error",
                    started_at=started_at,
                    ended_at=datetime.now(tz=timezone.utc),
                    error_summary=str(exc),
                )
            )
            return self._error_result(
                request_id=request_id,
                correlation_id=envelope.correlation_id,
                code="EXECUTION_FAILED",
                message=str(exc),
            )

        ended_at = datetime.now(tz=timezone.utc)
        self._emit_audit(
            AuditEvent(
                request_id=request_id,
                correlation_id=envelope.correlation_id,
                action=envelope.intent.action,
                sanitized_parameters=sanitized_params,
                status="success",
                started_at=started_at,
                ended_at=ended_at,
            )
        )

        return self._success_result(envelope.intent, outcome, request_id, envelope.correlation_id)

    def _success_result(
        self,
        intent: ActionIntent,
        outcome: dict[str, Any],
        request_id: str,
        correlation_id: str | None,
    ) -> ExecutionResult:
        return ExecutionResult(
            request_id=request_id,
            correlation_id=correlation_id,
            executed=True,
            status="success",
            actions=[{"action": intent.action, "status": "success", "result": outcome}],
            message=outcome.get("message") if isinstance(outcome.get("message"), str) else None,
            ui_hints=UIHints.model_validate(outcome["ui_hints"]) if isinstance(outcome.get("ui_hints"), dict) else None,
            tone_hints=ToneHints.model_validate(outcome["tone_hints"]) if isinstance(outcome.get("tone_hints"), dict) else None,
        )

    def _error_result(
        self,
        *,
        request_id: str,
        correlation_id: str | None,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> ExecutionResult:
        return ExecutionResult(
            request_id=request_id,
            correlation_id=correlation_id,
            executed=False,
            status="error",
            error=ExecutionError(code=code, message=message, details=details),
        )

    def _emit_audit(self, event: AuditEvent) -> None:
        audit_event(
            "orchestrator.execution",
            request_id=event.request_id,
            correlation_id=event.correlation_id,
            action=event.action,
            sanitized_parameters=event.sanitized_parameters,
            status=event.status,
            started_at=event.started_at.isoformat(),
            ended_at=event.ended_at.isoformat() if event.ended_at else None,
            error_summary=event.error_summary,
        )


def build_policy_decision(intent: ActionIntent) -> PolicyDecision:
    return evaluate_action(intent)
