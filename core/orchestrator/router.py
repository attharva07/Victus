from __future__ import annotations

from pydantic import BaseModel, ValidationError

from adapters.llm.provider import LLMProposer, ProposalResult
from core.camera.errors import CameraError
from core.camera.service import CameraService
from core.config import get_orchestrator_config
from core.filesystem.service import list_sandbox_files, read_sandbox_file, write_sandbox_file
from core.finance.service import add_transaction, list_transactions, summary
from core.logging.audit import audit_event, safe_excerpt, text_hash
from core.memory.service import add_memory, delete_memory, list_recent, search_memories
from core.orchestrator.deterministic import parse_intent
from core.orchestrator.policy import validate_intent
from core.orchestrator.schemas import (
    ActionResult,
    Intent,
    OrchestrateErrorResponse,
    OrchestrateRequest,
    OrchestrateResponse,
)

_ALLOWED_ACTIONS = [
    "noop",
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
    category: str
    merchant: str | None = None


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
}


def _deterministic_route(request: OrchestrateRequest) -> Intent | None:
    return parse_intent(request.normalized_text())


def _execute_intent(intent: Intent) -> tuple[str, list[ActionResult]]:
    action = intent.action
    params = intent.parameters
    if action == "camera.status":
        service = CameraService()
        status = service.status()
        result = ActionResult(action=action, parameters=params, result=status.model_dump())
        return status.message, [result]
    if action == "camera.capture":
        service = CameraService()
        try:
            capture = service.capture()
        except CameraError as exc:
            result = ActionResult(action=action, parameters=params, result={"error": str(exc)})
            return str(exc), [result]
        result = ActionResult(action=action, parameters=params, result=capture.model_dump())
        return "Captured image.", [result]
    if action == "camera.recognize":
        service = CameraService()
        try:
            recognition = service.recognize()
        except CameraError as exc:
            result = ActionResult(action=action, parameters=params, result={"error": str(exc)})
            return str(exc), [result]
        result = ActionResult(action=action, parameters=params, result=recognition.model_dump())
        return f"Detected {len(recognition.matches)} faces.", [result]
    if action == "memory.add":
        memory_id = add_memory(
            content=params["content"],
            tags=params.get("tags"),
            importance=params.get("importance", 5),
        )
        audit_event("orchestrate_memory_add", memory_id=memory_id)
        result = ActionResult(action=action, parameters=params, result={"id": memory_id})
        return f"Saved memory {memory_id}.", [result]
    if action == "memory.search":
        results = search_memories(query=params.get("query", ""), tags=params.get("tags"), limit=params.get("limit", 10))
        audit_event("orchestrate_memory_search", query=params.get("query", ""))
        result = ActionResult(action=action, parameters=params, result={"results": results})
        return f"Found {len(results)} memories.", [result]
    if action == "memory.list":
        results = list_recent(limit=params.get("limit", 20))
        audit_event("orchestrate_memory_list", limit=params.get("limit", 20))
        result = ActionResult(action=action, parameters=params, result={"results": results})
        return f"Listed {len(results)} memories.", [result]
    if action == "memory.delete":
        deleted = delete_memory(memory_id=params["id"])
        audit_event("orchestrate_memory_delete", memory_id=params["id"], deleted=deleted)
        result = ActionResult(action=action, parameters=params, result={"deleted": deleted})
        return ("Memory deleted." if deleted else "Memory not found."), [result]
    if action == "finance.add_transaction":
        amount = params["amount"]
        amount_cents = int(round(float(amount) * 100))
        transaction_id = add_transaction(
            amount_cents=amount_cents,
            category=params.get("category", "uncategorized"),
            merchant=params.get("merchant"),
        )
        audit_event("orchestrate_finance_add", transaction_id=transaction_id)
        result = ActionResult(
            action=action,
            parameters=params,
            result={"id": transaction_id, "amount_cents": amount_cents},
        )
        return f"Recorded transaction {transaction_id}.", [result]
    if action == "finance.list_transactions":
        results = list_transactions(limit=params.get("limit", 50), category=params.get("category"))
        audit_event("orchestrate_finance_list", count=len(results))
        result = ActionResult(action=action, parameters=params, result={"results": results})
        return f"Listed {len(results)} transactions.", [result]
    if action == "finance.summary":
        report = summary(period=params.get("period", "week"), group_by=params.get("group_by", "category"))
        audit_event("orchestrate_finance_summary", period=report["period"])
        result = ActionResult(action=action, parameters=params, result={"report": report})
        return "Generated finance summary.", [result]
    if action == "files.list":
        files = list_sandbox_files()
        result = ActionResult(action=action, parameters=params, result={"files": files})
        return f"Listed {len(files)} files.", [result]
    if action == "files.read":
        content = read_sandbox_file(params["path"])
        result = ActionResult(action=action, parameters=params, result={"content": content})
        return f"Read file {params['path']}.", [result]
    if action == "files.write":
        write_sandbox_file(params["path"], params.get("content", ""), params.get("mode", "overwrite"))
        result = ActionResult(action=action, parameters=params, result={"ok": True})
        return f"Wrote file {params['path']}.", [result]
    return "No action executed.", []


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
    schema = _ARG_SCHEMAS.get(proposal.action)
    if schema is None:
        return None
    try:
        parsed_args = schema.model_validate(proposal.args)
        return Intent(action=proposal.action, parameters=parsed_args.model_dump(), confidence=proposal.confidence)
    except ValidationError:
        return None


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


def route_intent(
    request: OrchestrateRequest, llm_provider: LLMProposer
) -> OrchestrateResponse | OrchestrateErrorResponse:
    config = get_orchestrator_config()
    text = request.normalized_text().strip()
    force_llm = bool(request.context.get("force_llm"))

    if not force_llm:
        deterministic_intent = _deterministic_route(request)
        if deterministic_intent is not None and deterministic_intent.confidence >= 1.0:
            deterministic_intent = validate_intent(deterministic_intent)
            if deterministic_intent.action != "noop":
                message, actions = _execute_intent(deterministic_intent)
                _log_orchestration_decision(
                    mode="deterministic",
                    llm_used=False,
                    selected_model=None,
                    action=deterministic_intent.action,
                    confidence=deterministic_intent.confidence,
                    executed=True,
                    error_type=None,
                )
                return OrchestrateResponse(
                    intent=deterministic_intent,
                    message=message,
                    actions=actions,
                    mode="deterministic",
                    executed=True,
                    result=actions[0].result if actions else None,
                )

    if not config.enable_llm_fallback:
        response = _unknown_intent_response(text)
        _log_orchestration_decision(
            mode="deterministic",
            llm_used=False,
            selected_model=None,
            action="noop",
            confidence=0.0,
            executed=False,
            error_type=response.error,
        )
        return response

    audit_event(
        "llm.propose.request",
        text_hash=text_hash(text),
        text_excerpt=safe_excerpt(text),
        domain=request.domain,
        candidate_count=len(_ALLOWED_ACTIONS),
    )
    proposal = llm_provider.propose(text=text, domain=request.domain, candidates=_ALLOWED_ACTIONS, context=request.context)
    audit_event(
        "llm.propose.result",
        ok=proposal.ok,
        action=proposal.action,
        confidence=proposal.confidence,
        reason=safe_excerpt(proposal.reason, max_len=120),
        selected_model=proposal.selected_model,
    )

    if not proposal.llm_used and proposal.reason in {"ollama_unreachable", "ollama_no_model", "provider_stub", "llm_disabled"}:
        response = _unknown_intent_response(text)
        _log_orchestration_decision(
            mode="deterministic",
            llm_used=False,
            selected_model=proposal.selected_model,
            action="noop",
            confidence=0.0,
            executed=False,
            error_type=response.error,
        )
        return response

    validated_intent = _validate_proposal(proposal)
    if validated_intent is None:
        response = _clarify_response(proposal.clarify_question)
        _log_orchestration_decision(
            mode="llm_proposal",
            llm_used=proposal.llm_used,
            selected_model=proposal.selected_model,
            action=proposal.action or "noop",
            confidence=proposal.confidence,
            executed=False,
            error_type=response.error,
        )
        return response

    validated_intent = validate_intent(validated_intent)
    confidence = validated_intent.confidence

    if confidence >= config.conf_execute and validated_intent.action != "noop":
        message, actions = _execute_intent(validated_intent)
        _log_orchestration_decision(
            mode="llm_proposal",
            llm_used=proposal.llm_used,
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
            result=actions[0].result if actions else None,
        )

    if confidence >= config.conf_propose:
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
            result=None,
        )
        _log_orchestration_decision(
            mode="llm_proposal",
            llm_used=proposal.llm_used,
            selected_model=proposal.selected_model,
            action=validated_intent.action,
            confidence=confidence,
            executed=False,
            error_type=None,
        )
        return response

    response = _clarify_response(
        proposal.clarify_question
        or "Do you want memory, finance, files, or camera? For example: 'remember ...' or 'spent 8 on coffee'."
    )
    _log_orchestration_decision(
        mode="llm_proposal",
        llm_used=proposal.llm_used,
        selected_model=proposal.selected_model,
        action=validated_intent.action,
        confidence=confidence,
        executed=False,
        error_type=response.error,
    )
    return response
