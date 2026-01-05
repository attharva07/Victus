from __future__ import annotations

"""Victus Phase 1 application scaffold.

This module wires together the router, planner, policy engine, executor, and
audit logger. It demonstrates the enforced flow: Input -> Plan -> Policy ->
Approval -> Execute -> Audit. Real interfaces (UI/voice/hotkey) will call into
`VictusApp.run_request` in later phases.
"""

from dataclasses import replace
from pathlib import Path
from typing import Callable, Dict, Sequence

from .core.approval import issue_approval
from .core.audit import AuditLogger
from .core.failures import FailureEvent, FailureLogger, hash_stack, safe_user_intent
from .core.executor import ExecutionEngine
from .core.intent_router import route_intent
from .core.planner import Planner
from .core.policy import PolicyEngine
from .core.router import Router
from .core.sanitization import sanitize_plan
from .core.schemas import Approval, Context, Plan, PlanStep, PolicyError
from .domains.base import BasePlugin
from .config.runtime import get_llm_provider, is_outbound_llm_provider


class VictusApp:
    def __init__(
        self,
        plugins: Dict[str, BasePlugin],
        policy_engine: PolicyEngine | None = None,
        audit_logger: AuditLogger | None = None,
    ) -> None:
        self.router = Router()
        self.planner = Planner()
        self.policy_engine = policy_engine or PolicyEngine()
        self.executor = ExecutionEngine(plugins, signature_secret=self.policy_engine.signature_secret)
        self.audit = audit_logger or AuditLogger()
        self.failure_logger = FailureLogger(Path("victus/data/failures"))

    def build_plan(self, goal: str, domain: str, steps: Sequence[PlanStep], **kwargs) -> Plan:
        """Create a plan using the deterministic planner stub."""

        return self.planner.build_plan(goal=goal, domain=domain, steps=steps, **kwargs)

    def prepare_plan_for_policy(self, plan: Plan) -> Plan:
        """Mark outbound flows and redact sensitive arguments before policy review."""

        return sanitize_plan(plan)

    def request_approval(self, plan: Plan, context: Context) -> tuple[Plan, Approval]:
        """Prepare and submit a plan for approval, returning the redacted copy."""

        prepared_plan = self.prepare_plan_for_policy(plan)
        approval = issue_approval(prepared_plan, context, self.policy_engine)
        return prepared_plan, approval

    def execute_plan(self, plan: Plan, approval: Approval) -> Dict[str, object]:
        """Execute an approved plan via the execution engine."""

        return self.executor.execute(plan, approval)

    def execute_plan_streaming(
        self,
        plan: Plan,
        approval: Approval,
        *,
        stream_callbacks: Dict[str, Callable[[str], None]] | None = None,
        stop_requests: Dict[str, Callable[[], bool]] | None = None,
    ) -> Dict[str, object]:
        """Execute a plan while streaming results to provided callbacks."""

        return self.executor.execute_streaming(
            plan,
            approval,
            stream_callbacks=stream_callbacks,
            stop_requests=stop_requests,
        )

    def run_request(self, user_input: str, context: Context, domain: str, steps: Sequence[PlanStep]) -> Dict[str, object]:
        """Run the full request lifecycle and record an audit entry."""

        try:
            routed = self.router.route(user_input, context)
            routed_action = route_intent(user_input, safety_filter=self.router.safety_filter)
            if routed_action:
                plan = Plan(
                    goal=user_input,
                    domain="system",
                    steps=[PlanStep(id="step-1", tool="system", action=routed_action.action, args=routed_action.args)],
                    risk="low",
                    origin="router",
                )
            else:
                plan = self.build_plan(goal=user_input, domain=domain, steps=steps)
            prepared_plan, approval = self.request_approval(plan, routed.context)
            results = self.execute_plan(prepared_plan, approval)
            self.audit.log_request(
                user_input=user_input,
                plan=prepared_plan,
                approval=approval,
                results=results,
                errors=None,
            )
            return results
        except Exception as exc:  # noqa: BLE001
            self._log_failure(user_input, context, domain, steps, exc)
            if isinstance(exc, PolicyError):
                raise
            return {"error": "request_failed", "message": "The request could not be completed safely."}

    def run_request_streaming(
        self,
        user_input: str,
        context: Context,
        domain: str,
        steps: Sequence[PlanStep],
        *,
        stream_callbacks: Dict[str, Callable[[str], None]] | None = None,
        stop_requests: Dict[str, Callable[[], bool]] | None = None,
    ) -> Dict[str, object]:
        """Run the request lifecycle while streaming step outputs.

        This mirrors ``run_request`` but dispatches steps through
        ``execute_plan_streaming`` so that UI callers can append output
        incrementally without blocking the main thread.
        """

        try:
            routed = self.router.route(user_input, context)
            routed_action = route_intent(user_input, safety_filter=self.router.safety_filter)
            if routed_action:
                plan = Plan(
                    goal=user_input,
                    domain="system",
                    steps=[PlanStep(id="step-1", tool="system", action=routed_action.action, args=routed_action.args)],
                    risk="low",
                    origin="router",
                )
            else:
                plan = self.build_plan(goal=user_input, domain=domain, steps=steps)
            prepared_plan, approval = self.request_approval(plan, routed.context)
            results = self.execute_plan_streaming(
                prepared_plan,
                approval,
                stream_callbacks=stream_callbacks,
                stop_requests=stop_requests,
            )
            self.audit.log_request(
                user_input=user_input,
                plan=prepared_plan,
                approval=approval,
                results=results,
                errors=None,
            )
            return results
        except Exception as exc:  # noqa: BLE001
            self._log_failure(user_input, context, domain, steps, exc)
            if isinstance(exc, PolicyError):
                raise
            return {"error": "request_failed", "message": "The request could not be completed safely."}

    @staticmethod
    def _mark_openai_outbound(plan: Plan) -> Plan:
        provider = get_llm_provider()
        is_outbound = is_outbound_llm_provider(provider)
        outbound = replace(
            plan.data_outbound,
            to_openai=is_outbound and any(step.tool == "openai" for step in plan.steps),
            redaction_required=is_outbound and plan.data_outbound.redaction_required,
        )
        return replace(plan, data_outbound=outbound)

    @staticmethod
    def _redact_value(key: str, value: object) -> object:
        if not isinstance(value, str):
            return value
        if key == "to":
            return "redacted@example.com"
        return "[REDACTED]"

    def _redact_openai_steps(self, plan: Plan) -> Plan:
        if not plan.data_outbound.redaction_required:
            return plan

        redacted_steps = []
        for step in plan.steps:
            if step.tool != "openai":
                redacted_steps.append(step)
                continue
            redacted_args = {key: self._redact_value(key, value) for key, value in step.args.items()}
            redacted_steps.append(replace(step, args=redacted_args))

        return replace(plan, steps=redacted_steps)

    def _log_failure(self, user_input: str, context: Context, domain: str, steps: Sequence[PlanStep], exc: Exception) -> None:
        action_name = steps[0].action if steps else "run_request"
        event = FailureEvent(
            stage="2",
            phase="1",
            domain=domain,
            component="executor",
            severity="high",
            category="runtime_error",
            request_id=getattr(context, "session_id", ""),
            user_intent=safe_user_intent(user_input),
            action={"name": action_name, "args_redacted": True},
            failure={
                "code": "request_pipeline_error",
                "message": safe_user_intent(str(exc)),
                "exception_type": exc.__class__.__name__,
                "stack_hash": hash_stack(exc),
                "details_redacted": True,
            },
            expected_behavior="Request should complete without uncaught exceptions",
            remediation_hint="Inspect recurring stack hashes and add guards",
            resolution={"status": "new", "resolved_ts": None, "notes": None},
            tags=[domain],
        )
        self.failure_logger.append(event)
