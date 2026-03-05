from __future__ import annotations

import re
from datetime import datetime, timezone

from pydantic import BaseModel, ValidationError

from adapters.llm.provider import LLMProposer, ProposalResult
from core.cognition import CognitionEngine, InMemorySessionStateStore
from core.config import get_orchestrator_config
from core.logging.audit import audit_event, safe_excerpt, text_hash
from core.orchestrator.registry import TOOL_REGISTRY
from core.orchestrator.deterministic import parse_intent
from core.orchestrator.policy import enforce_policy_gate, validate_intent
from core.signals.extractors import extract_signals
from core.signals.models import SignalBundle
from core.orchestrator.schemas import (
    ActionResult,
    Intent,
    OrchestrateErrorResponse,
    OrchestrateRequest,
    OrchestrateResponse,
)

_ALLOWED_ACTIONS = [
    "noop",
    "chat.reply",
    "camera.status",
    "camera.capture",
    "camera.recognize",
    "memory.add",
    "memory.search",
    "memory.list",
    "memory.delete",
    "finance.add_transaction",
    "finance.list_transactions",
    "finance.summary",
    "files.list",
    "files.read",
    "files.write",
]


class _MemoryAddArgs(BaseModel):
    content: str
    tags: list[str] | None = None
    importance: int | None = None


class _MemorySearchArgs(BaseModel):
    query: str = ""
    tags: list[str] | None = None
    limit: int = 10


class _MemoryListArgs(BaseModel):
    limit: int = 20


class _MemoryDeleteArgs(BaseModel):
    id: str


class _FinanceAddArgs(BaseModel):
    amount: float
    category: str = "uncategorized"
    merchant: str | None = None
    currency: str = "USD"
    occurred_at: str | None = None


class _FinanceListArgs(BaseModel):
    category: str | None = None
    limit: int = 50


class _FinanceSummaryArgs(BaseModel):
    period: str = "week"
    group_by: str = "category"


class _FilesReadArgs(BaseModel):
    path: str


class _FilesWriteArgs(BaseModel):
    path: str
    content: str = ""
    mode: str = "overwrite"


class _FilesListArgs(BaseModel):
    pass


class _CameraStatusArgs(BaseModel):
    pass


class _CameraCaptureArgs(BaseModel):
    pass


class _CameraRecognizeArgs(BaseModel):
    pass


class _ChatReplyArgs(BaseModel):
    pass


_ARG_SCHEMAS: dict[str, type[BaseModel]] = {
    "memory.add": _MemoryAddArgs,
    "memory.search": _MemorySearchArgs,
    "memory.list": _MemoryListArgs,
    "memory.delete": _MemoryDeleteArgs,
    "finance.add_transaction": _FinanceAddArgs,
    "finance.list_transactions": _FinanceListArgs,
    "finance.summary": _FinanceSummaryArgs,
    "files.read": _FilesReadArgs,
    "files.write": _FilesWriteArgs,
    "files.list": _FilesListArgs,
    "camera.status": _CameraStatusArgs,
    "camera.capture": _CameraCaptureArgs,
    "camera.recognize": _CameraRecognizeArgs,
    "chat.reply": _ChatReplyArgs,
}




_SMALLTALK_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^\s*(hi|hello|hey)\b", re.IGNORECASE),
    re.compile(r"\bhow are you\b", re.IGNORECASE),
    re.compile(r"\bwhat(?:'s| is) up\b", re.IGNORECASE),
    re.compile(r"^\s*good (morning|afternoon|evening)\b", re.IGNORECASE),
    re.compile(r"^\s*howdy\b", re.IGNORECASE),
)

_TOOL_DOMAIN_HINTS = {
    "memory": ("memory", "remember", "recall", "forget"),
    "finance": ("finance", "spent", "paid", "transaction", "summary", "$"),
    "files": ("file", "files", "read", "write", "append", "list"),
    "camera": ("camera", "photo", "picture", "capture", "recognize", "face"),
}

_SESSION_STORE = InMemorySessionStateStore()
_COGNITION = CognitionEngine(state_store=_SESSION_STORE)


def _is_smalltalk(text: str) -> bool:
    normalized = text.strip()
    if not normalized:
        return False
    return any(pattern.search(normalized) for pattern in _SMALLTALK_PATTERNS)


def _deterministic_route(request: OrchestrateRequest) -> Intent | None:
    return parse_intent(request.normalized_text())


def _tool_domains_in_text(text: str) -> list[str]:
    lowered = text.lower()
    matches: list[str] = []
    for domain, hints in _TOOL_DOMAIN_HINTS.items():
        if any(hint in lowered for hint in hints):
            matches.append(domain)
    return matches


def _execute_intent(intent: Intent) -> tuple[str, list[ActionResult]]:
    action = intent.action
    params = intent.parameters
    handler = TOOL_REGISTRY.get(action)
    if handler is None:
        return "No action executed.", []
    message, result = handler(params)
    return message, [result]


def _unknown_intent_response(text: str) -> OrchestrateErrorResponse:
    if len(text.split()) < 3:
        return OrchestrateErrorResponse(
            error="clarify",
            message="Please provide more detail so I can route this deterministically.",
            fields={"text": "include an explicit action and target"},
        )
    return OrchestrateErrorResponse(
        error="unknown_intent",
        message="I could not deterministically map that request to a supported action.",
        candidates=["memory", "finance", "files", "camera"],
    )


def _clarify_response(question: str | None = None) -> OrchestrateErrorResponse:
    return OrchestrateErrorResponse(
        error="clarify",
        message=question or "Can you confirm if this is memory, finance, files, or camera?",
        candidates=["memory.add", "finance.add_transaction", "files.read", "camera.status"],
    )


def _validate_proposal(proposal: ProposalResult) -> Intent | None:
    if not proposal.ok or proposal.action is None:
        return None
    if proposal.action not in _ALLOWED_ACTIONS:
        return None
    raw_args = proposal.args if isinstance(proposal.args, dict) else {}
    return Intent(action=proposal.action, parameters=dict(raw_args), confidence=proposal.confidence)


def _noop_response(message: str, trace: dict[str, object] | None) -> OrchestrateResponse:
    result: dict[str, object] = {}
    if trace is not None:
        result["trace"] = trace
    return OrchestrateResponse(
        intent=Intent(action="noop", parameters={}, confidence=0.0),
        message=message,
        actions=[],
        mode="deterministic",
        executed=False,
        result=result or None,
    )


def _regex_finance_candidate(text: str) -> Intent | None:
    patterns = (
        re.compile(r"\b(?:i\s+)?(?:spent|paid)\s+(?P<currency>[$€£])?(?P<amount>\d+(?:\.\d{1,2})?)(?:\s*(?:dollars?|bucks))?\s+(?:at|for|on)\s+(?P<merchant>.+)$", re.IGNORECASE),
        re.compile(r"\badd\s+transaction\s+(?P<currency>[$€£])?(?P<amount>\d+(?:\.\d{1,2})?)\s+(?:for\s+)?(?P<merchant>.+)$", re.IGNORECASE),
    )
    for pattern in patterns:
        match = pattern.search(text.strip())
        if not match:
            continue
        amount = float(match.group("amount"))
        merchant = match.group("merchant").strip(" .,!?")
        if not merchant:
            continue
        symbol = (match.groupdict().get("currency") or "$").strip()
        currency = {"$": "USD", "€": "EUR", "£": "GBP"}.get(symbol, "USD")
        return Intent(
            action="finance.add_transaction",
            parameters={
                "amount": amount,
                "merchant": merchant,
                "category": merchant,
                "currency": currency,
                "occurred_at": datetime.now(tz=timezone.utc).isoformat(),
            },
            confidence=0.92,
        )
    return None


def _response_result(
    actions: list[ActionResult],
    trace: dict[str, object] | None,
) -> dict[str, object] | None:
    result: dict[str, object] = {}
    if actions and actions[0].result:
        result.update(actions[0].result)
    if trace is not None:
        result["trace"] = trace
    return result or None


def _log_orchestration_decision(
    *,
    mode: str,
    llm_used: bool,
    selected_model: str | None,
    action: str,
    confidence: float,
    executed: bool,
    error_type: str | None,
) -> None:
    audit_event(
        "orchestrate.decision",
        mode=mode,
        llm_used=llm_used,
        selected_model=selected_model,
        action=action,
        confidence=confidence,
        executed=executed,
        error_type=error_type,
    )


def allowed_actions() -> list[str]:
    return list(_ALLOWED_ACTIONS)


def _apply_cognitive_layer(
    *,
    intent: Intent,
    text: str,
    signals: SignalBundle,
    context: dict[str, object],
    decision_path: list[str],
) -> tuple[Intent | None, dict[str, object]]:
    cognition = _COGNITION.run(
        session_id=str(context.get("session_id", "default")),
        text=text,
        context={
            "hinted_action": intent.action if intent.action not in {"unknown.action", "noop"} else "",
            "hinted_parameters": intent.parameters,
            "confirmation_token": context.get("confirmation_token"),
            "cognition_config": {"blocked_actions": ["admin.delete_user"]},
        },
        memory_candidates=list(context.get("memory_candidates", [])),
    )
    policy = enforce_policy_gate(
        action=cognition.intent.action,
        risk=cognition.decision.risk,
        confirmation_token=str(context.get("confirmation_token") or ""),
    )
    decision_path.append(f"cognition:mode:{cognition.decision.mode}")
    if cognition.decision.mode in {"clarify", "refuse", "suggest"} or not policy.action_allowed:
        return None, cognition.model_dump()
    schema = _ARG_SCHEMAS.get(cognition.intent.action)
    if schema is None:
        return None, cognition.model_dump() | {"error": "action_not_executable"}
    try:
        parsed_args = schema.model_validate(cognition.intent.parameters)
    except ValidationError:
        return None, cognition.model_dump() | {"error": "invalid_candidate_parameters"}
    return Intent(action=cognition.intent.action, parameters=parsed_args.model_dump(), confidence=cognition.intent.confidence), cognition.model_dump()


def route_intent(
    request: OrchestrateRequest, llm_provider: LLMProposer
) -> OrchestrateResponse | OrchestrateErrorResponse:
    config = get_orchestrator_config()
    text = request.normalized_text().strip()
    force_llm = bool(request.context.get("force_llm"))
    debug_enabled = bool(request.context.get("debug"))
    selected_model: str | None = None
    proposal_confidence: float | None = None
    llm_was_called = False
    decision_path: list[str] = []
    signals = extract_signals(text)
    debug_extras: dict[str, object] = {}

    def _trace(router_mode: str) -> dict[str, object] | None:
        if not debug_enabled:
            return None
        return {
            "router_mode": router_mode,
            "llm_enabled": config.llm_enabled,
            "selected_model": selected_model,
            "proposal_confidence": proposal_confidence,
            "autoexec": config.llm_allow_autoexec,
            "thresholds": {"execute": config.conf_execute, "propose": config.conf_propose},
            "decision_path": decision_path,
            **debug_extras,
        }

    if debug_enabled:
        debug_extras["signals"] = signals.model_dump()

    if not force_llm:
        deterministic_intent = _deterministic_route(request)
        cognition_meta: dict[str, object] | None = None
        if deterministic_intent is not None and deterministic_intent.confidence >= 1.0:
            decision_path.append("deterministic:tool_match")
            explicit_error = deterministic_intent.parameters.get("error")
            if deterministic_intent.action == "noop" and isinstance(explicit_error, str):
                message = deterministic_intent.parameters.get("message")
                if explicit_error == "clarify":
                    return _clarify_response(message if isinstance(message, str) else None)
                if explicit_error == "unknown_intent":
                    return OrchestrateErrorResponse(
                        error="unknown_intent",
                        message=message if isinstance(message, str) else "Unsupported explicit action.",
                    )
            selected_intent, cognition_meta = _apply_cognitive_layer(
                intent=deterministic_intent,
                text=text,
                context=request.context,
                signals=signals,
                decision_path=decision_path,
            )
            if debug_enabled:
                debug_extras["cognition"] = cognition_meta
            if selected_intent is not None:
                selected_intent = validate_intent(selected_intent)
            if selected_intent is not None and selected_intent.action != "noop":
                message, actions = _execute_intent(selected_intent)
                _log_orchestration_decision(
                    mode="deterministic",
                    llm_used=False,
                    selected_model=None,
                    action=selected_intent.action,
                    confidence=selected_intent.confidence,
                    executed=True,
                    error_type=None,
                )
                result = _response_result(actions, _trace("deterministic")) or {}
                result["cognition"] = cognition_meta
                return OrchestrateResponse(
                    intent=selected_intent,
                    message=message,
                    actions=actions,
                    mode="deterministic",
                    executed=True,
                    result=result,
                )
            if selected_intent is None:
                question = cognition_meta.get("decision", {}).get("clarification_question") if isinstance(cognition_meta, dict) else None
                if cognition_meta.get("decision", {}).get("requires_confirmation"):
                    return _clarify_response("High-risk action detected. Reply with CONFIRM to continue.")
                return _clarify_response(question if isinstance(question, str) else None)

        regex_finance_intent = _regex_finance_candidate(text)
        if regex_finance_intent is not None:
            decision_path.append("deterministic:regex_finance_candidate")
            selected_intent, cognition_meta = _apply_cognitive_layer(
                intent=regex_finance_intent,
                text=text,
                context=request.context,
                signals=signals,
                decision_path=decision_path,
            )
            if debug_enabled:
                debug_extras["cognition"] = cognition_meta
            if selected_intent is not None:
                selected_intent = validate_intent(selected_intent)
            if selected_intent is not None and selected_intent.action != "noop":
                message, actions = _execute_intent(selected_intent)
                _log_orchestration_decision(
                    mode="deterministic",
                    llm_used=False,
                    selected_model=None,
                    action=selected_intent.action,
                    confidence=selected_intent.confidence,
                    executed=True,
                    error_type=None,
                )
                result = _response_result(actions, _trace("deterministic")) or {}
                result["cognition"] = cognition_meta
                return OrchestrateResponse(
                    intent=selected_intent,
                    message=message,
                    actions=actions,
                    mode="deterministic",
                    executed=True,
                    result=result,
                )
            if selected_intent is None:
                question = cognition_meta.get("decision", {}).get("clarification_question") if isinstance(cognition_meta, dict) else None
                if cognition_meta.get("decision", {}).get("requires_confirmation"):
                    return _clarify_response("High-risk action detected. Reply with CONFIRM to continue.")
                return _clarify_response(question if isinstance(question, str) else None)

        tool_domains = _tool_domains_in_text(text)
        if not tool_domains:
            decision_path.append("deterministic:noop_non_tool")
            return _noop_response("Please ask for a supported tool action (memory, finance, files, or camera).", _trace("deterministic"))

        if deterministic_intent is None and not config.enable_llm_fallback:
            decision_path.append("deterministic:no_match")
            selected_intent, cognition_meta = _apply_cognitive_layer(
                intent=Intent(action="unknown.action", parameters={}, confidence=0.0),
                text=text,
                context=request.context,
                signals=signals,
                decision_path=decision_path,
            )
            if selected_intent is None:
                if cognition_meta.get("decision", {}).get("requires_confirmation"):
                    return _clarify_response("High-risk action detected. Reply with CONFIRM to continue.")
                question = cognition_meta.get("decision", {}).get("clarification_question") if isinstance(cognition_meta, dict) else None
                return _clarify_response(question if isinstance(question, str) else None)
            selected_intent = validate_intent(selected_intent)
            if selected_intent.action != "noop":
                message, actions = _execute_intent(selected_intent)
                _log_orchestration_decision(
                    mode="deterministic",
                    llm_used=False,
                    selected_model=None,
                    action=selected_intent.action,
                    confidence=selected_intent.confidence,
                    executed=True,
                    error_type=None,
                )
                result = _response_result(actions, _trace("deterministic")) or {}
                result["cognition"] = cognition_meta
                return OrchestrateResponse(
                    intent=selected_intent,
                    message=message,
                    actions=actions,
                    mode="deterministic",
                    executed=True,
                    result=result,
                )

        if len(tool_domains) > 1:
            decision_path.append("deterministic:clarify")
            if not config.enable_llm_fallback:
                return _clarify_response("I can help with tools—do you want memory, finance, files, or camera?")

    if not config.enable_llm_fallback:
        decision_path.append("fallback:clarify_no_llm")
        _log_orchestration_decision(
            mode="deterministic",
            llm_used=False,
            selected_model=None,
            action="noop",
            confidence=0.0,
            executed=False,
            error_type=None,
        )
        return _noop_response("I need a concrete tool request to continue.", _trace("chat_fallback"))

    audit_event(
        "llm.propose.request",
        text_hash=text_hash(text),
        text_excerpt=safe_excerpt(text),
        domain=request.domain,
        candidate_count=len(_ALLOWED_ACTIONS),
    )
    proposal = llm_provider.propose(text=text, domain=request.domain, candidates=_ALLOWED_ACTIONS, context=request.context)
    decision_path.append("llm:propose")
    llm_was_called = True
    selected_model = proposal.selected_model
    proposal_confidence = proposal.confidence
    audit_event(
        "llm.propose.result",
        ok=proposal.ok,
        action=proposal.action,
        confidence=proposal.confidence,
        reason=safe_excerpt(proposal.reason, max_len=120),
        selected_model=proposal.selected_model,
    )

    if not proposal.llm_used and proposal.reason in {"ollama_unreachable", "ollama_no_model", "provider_stub", "llm_disabled"}:
        decision_path.append("llm:unavailable_clarify")
        _log_orchestration_decision(
            mode="deterministic",
            llm_used=llm_was_called,
            selected_model=proposal.selected_model,
            action="noop",
            confidence=0.0,
            executed=False,
            error_type=None,
        )
        return _noop_response("I need a concrete tool request to continue.", _trace("chat_fallback"))

    if proposal.action is not None and proposal.action not in _ALLOWED_ACTIONS:
        decision_path.append("llm:disallowed_action")
        response = _unknown_intent_response(text)
        _log_orchestration_decision(
            mode="llm_proposal",
            llm_used=llm_was_called,
            selected_model=proposal.selected_model,
            action=proposal.action,
            confidence=proposal.confidence,
            executed=False,
            error_type=response.error,
        )
        return response

    proposed_intent = _validate_proposal(proposal)
    if proposed_intent is None:
        decision_path.append("llm:invalid_or_unparseable")
        proposed_intent = Intent(action="unknown.action", parameters={}, confidence=proposal.confidence)

    selected_intent, cognition_meta = _apply_cognitive_layer(
        intent=proposed_intent,
        text=text,
        context=request.context,
        signals=signals,
        decision_path=decision_path,
    )
    if debug_enabled:
        debug_extras["cognition"] = cognition_meta
    if selected_intent is None:
        if cognition_meta.get("decision", {}).get("requires_confirmation"):
            return _clarify_response("High-risk action detected. Reply with CONFIRM to continue.")
        question = cognition_meta.get("decision", {}).get("clarification_question") if isinstance(cognition_meta, dict) else None
        return _clarify_response(question if isinstance(question, str) else "I need clarification because no allowed candidate action remained.")
    validated_intent = validate_intent(selected_intent)
    confidence = validated_intent.confidence

    if validated_intent.action == "chat.reply":
        decision_path.append("llm:chat_reply_blocked")
        return _clarify_response("Please request a supported tool action instead of open-ended chat.")

    should_auto_execute = (
        config.llm_allow_autoexec and confidence >= config.conf_execute and validated_intent.action != "noop"
    )
    if should_auto_execute:
        decision_path.append("llm:auto_execute")
        message, actions = _execute_intent(validated_intent)
        _log_orchestration_decision(
            mode="llm_proposal",
            llm_used=llm_was_called,
            selected_model=proposal.selected_model,
            action=validated_intent.action,
            confidence=confidence,
            executed=True,
            error_type=None,
        )
        return OrchestrateResponse(
            intent=validated_intent,
            message=message,
            actions=actions,
            mode="llm_proposal",
            proposed_action={
                "action": validated_intent.action,
                "parameters": validated_intent.parameters,
                "confidence": confidence,
            },
            executed=True,
            result=(_response_result(actions, _trace("llm_proposal")) or {}) | {"cognition": cognition_meta},
        )

    if confidence >= config.conf_propose:
        decision_path.append("llm:proposal_requires_approval")
        response = OrchestrateResponse(
            intent=validated_intent,
            message="I can do this next. Please approve execution.",
            actions=[],
            mode="llm_proposal",
            proposed_action={
                "action": validated_intent.action,
                "parameters": validated_intent.parameters,
                "confidence": confidence,
            },
            executed=False,
            result=(({"trace": trace} if (trace := _trace("llm_proposal")) is not None else {}) | {"cognition": cognition_meta}) or None,
        )
        _log_orchestration_decision(
            mode="llm_proposal",
            llm_used=llm_was_called,
            selected_model=proposal.selected_model,
            action=validated_intent.action,
            confidence=confidence,
            executed=False,
            error_type=None,
        )
        return response

    _log_orchestration_decision(
        mode="llm_proposal",
        llm_used=llm_was_called,
        selected_model=proposal.selected_model,
        action=validated_intent.action,
        confidence=confidence,
        executed=False,
        error_type=None,
    )
    decision_path.append("llm:low_confidence_noop")
    return _noop_response("I need a concrete tool request to continue.", _trace("chat_fallback"))
