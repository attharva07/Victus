from __future__ import annotations

import base64
import secrets
from pathlib import Path

import bcrypt
from fastapi import Body, Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from core.finance.policy import FinanceNotFoundError, FinancePolicyError, FinanceValidationError
from core.finance.schemas import AccountUpsert, SpendingSummaryRequest, TransactionUpdate, TransactionWrite

from victus.ui_state import (
    DialogueSendRequest,
    UIState,
    WorkflowActionRequest,
    approval_decision,
    dialogue_send,
    fetch_ui_state,
    init_ui_state_db,
    mark_reminder_done,
    workflow_action,
)

from adapters.llm.provider import LLMProvider
from core.camera.models import CameraStatus, CaptureResponse, RecognizeResponse
from core.camera.service import CameraService
from core.config import ensure_directories, get_orchestrator_config
from core.filesystem.sandbox import FileSandboxError
from core.filesystem.service import list_sandbox_files, read_sandbox_file, write_sandbox_file
from core.finance.service import (
    add_transaction,
    category_summary,
    delete_transaction,
    generate_finance_brief,
    get_rule_thresholds,
    get_transaction,
    list_alerts,
    list_behavior_logs,
    list_transactions,
    set_rule_threshold,
    spending_summary,
    summary,
    update_transaction,
    upsert_account,
)
from core.logging.audit import audit_event, safe_excerpt, text_hash
from core.logging.logger import get_logger
from core.memory.service import add_memory, delete_memory, list_recent, search_memories
from core.orchestrator.router import allowed_actions, route_intent
from core.orchestrator.schemas import OrchestrateErrorResponse, OrchestrateRequest, OrchestrateResponse
from core.errors import VictusError, sanitize_exception
from core.security.auth import login_user, require_user
from core.security.bootstrap_store import is_bootstrapped, set_bootstrap


class LoginRequest(BaseModel):
    username: str
    password: str


class BootstrapInitRequest(BaseModel):
    username: str
    password: str


class BootstrapInitResponse(BaseModel):
    ok: bool
    bootstrapped: bool


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MemoryAddRequest(BaseModel):
    content: str
    type: str = "note"
    tags: list[str] | None = None
    importance: int = 5
    confidence: float = 0.8
    sensitivity: str | None = None


class FinanceAddRequest(TransactionWrite):
    pass


class FinanceUpdateRequest(TransactionUpdate):
    pass


class FinanceAccountRequest(AccountUpsert):
    pass


class FileWriteRequest(BaseModel):
    path: str
    content: str
    mode: str = "overwrite"


class FinanceRuleUpdateRequest(BaseModel):
    rule_key: str
    threshold_value: float
    enabled: bool = True


class FinanceBriefRequest(BaseModel):
    cards: list[dict[str, object]] = Field(default_factory=list)
    budget: dict[str, object] = Field(default_factory=dict)
    savings_goals: list[dict[str, object]] = Field(default_factory=list)
    holdings: list[dict[str, object]] = Field(default_factory=list)
    watchlist: list[dict[str, object]] = Field(default_factory=list)
    paycheck_days: list[int] | None = None


class CameraCaptureRequest(BaseModel):
    reason: str | None = None
    format: str = "jpg"


class CameraRecognizeRequest(BaseModel):
    capture_id: str | None = None
    image_b64: str | None = None


def _request_id(request: Request) -> str | None:
    return request.headers.get("X-Request-ID") or request.headers.get("X-Request-Id")


def create_app() -> FastAPI:
    ensure_directories()
    get_logger()
    app = FastAPI(title="Victus Local")

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        err = sanitize_exception(exc)
        if isinstance(exc, FinanceValidationError):
            status_code = status.HTTP_400_BAD_REQUEST
        elif isinstance(exc, FinanceNotFoundError):
            status_code = status.HTTP_404_NOT_FOUND
        elif isinstance(exc, FinancePolicyError):
            status_code = status.HTTP_403_FORBIDDEN
        else:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return JSONResponse(status_code=status_code, content=err.to_response())
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    init_ui_state_db()
    llm_provider = LLMProvider()
    camera_service = CameraService()
    dist_dir = Path(__file__).resolve().parents[2] / "apps" / "web" / "dist"

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}


    @app.get("/api/health")
    def api_health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/ui/state", response_model=UIState)
    def api_ui_state() -> UIState:
        return fetch_ui_state()

    @app.post("/api/approvals/{approval_id}/approve", response_model=UIState)
    def api_approval_approve(approval_id: str) -> UIState:
        return approval_decision(approval_id, "approved")

    @app.post("/api/approvals/{approval_id}/deny", response_model=UIState)
    def api_approval_deny(approval_id: str) -> UIState:
        return approval_decision(approval_id, "denied")

    @app.post("/api/reminders/{reminder_id}/done", response_model=UIState)
    def api_reminder_done(reminder_id: str) -> UIState:
        return mark_reminder_done(reminder_id)

    @app.post("/api/workflows/{workflow_id}/action", response_model=UIState)
    def api_workflow_action(workflow_id: str, payload: WorkflowActionRequest) -> UIState:
        return workflow_action(workflow_id, payload.action)

    @app.post("/api/dialogue/send", response_model=UIState)
    def api_dialogue_send(payload: DialogueSendRequest) -> UIState:
        return dialogue_send(payload.message)

    @app.post("/login", response_model=LoginResponse)
    def login(payload: LoginRequest) -> LoginResponse:
        token = login_user(payload.username, payload.password)
        return LoginResponse(access_token=token)

    @app.get("/bootstrap/status")
    def bootstrap_status() -> dict[str, bool]:
        return {"bootstrapped": is_bootstrapped()}

    @app.post("/bootstrap/init", response_model=BootstrapInitResponse)
    def bootstrap_init(payload: BootstrapInitRequest, request: Request) -> BootstrapInitResponse:
        request_id = _request_id(request)
        if is_bootstrapped():
            audit_event("bootstrap_init", ok=False, request_id=request_id, reason="already_bootstrapped")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "already_bootstrapped",
                    "message": "Victus Local has already been bootstrapped.",
                },
            )
        if payload.username != "admin":
            audit_event("bootstrap_init", ok=False, request_id=request_id, reason="invalid_username")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "invalid_username", "message": "Only the 'admin' username is allowed."},
            )
        if len(payload.password) < 12:
            audit_event("bootstrap_init", ok=False, request_id=request_id, reason="weak_password")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "weak_password", "message": "Password must be at least 12 characters."},
            )

        password_hash = bcrypt.hashpw(payload.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        secret_bytes = secrets.token_bytes(32)
        jwt_secret = base64.urlsafe_b64encode(secret_bytes).decode("utf-8")
        set_bootstrap(password_hash, jwt_secret)
        audit_event("bootstrap_init", ok=True, request_id=request_id, username=payload.username)
        return BootstrapInitResponse(ok=True, bootstrapped=True)

    @app.get("/me")
    def me(user: str = Depends(require_user)) -> dict[str, str]:
        return {"username": user}

    @app.get("/debug/orchestrator")
    def debug_orchestrator(user: str = Depends(require_user)) -> dict[str, object]:
        _ = user
        orchestrator_config = get_orchestrator_config()
        debug_status = llm_provider.debug_status(llm_enabled=orchestrator_config.llm_enabled)
        return {
            "llm_enabled": orchestrator_config.llm_enabled,
            "provider": debug_status["provider"],
            "selected_model": debug_status["selected_model"],
            "model_priority": list(orchestrator_config.model_priority),
            "thresholds": {
                "execute": orchestrator_config.conf_execute,
                "propose": orchestrator_config.conf_propose,
            },
            "last_error": debug_status.get("last_error"),
            "allowed_actions": allowed_actions(),
        }

    @app.post(
        "/orchestrate",
        response_model=OrchestrateResponse | OrchestrateErrorResponse,
        responses={200: {"model": OrchestrateErrorResponse}},
    )
    def orchestrate(
        payload: OrchestrateRequest, user: str = Depends(require_user)
    ) -> OrchestrateResponse | OrchestrateErrorResponse:
        user_text = payload.normalized_text()
        audit_event(
            "orchestrate_requested",
            username=user,
            text_hash=text_hash(user_text),
            text_excerpt=safe_excerpt(user_text),
        )
        return route_intent(payload, llm_provider)

    @app.post("/memory/add")
    def memory_add(payload: MemoryAddRequest, user: str = Depends(require_user)) -> dict[str, str]:
        memory_id = add_memory(
            content=payload.content,
            type=payload.type,
            tags=payload.tags,
            source=user,
            importance=payload.importance,
            confidence=payload.confidence,
            sensitivity=payload.sensitivity,
        )
        return {"id": memory_id}

    @app.get("/memory/search")
    def memory_search(
        q: str = Query(..., alias="q"),
        tag: list[str] | None = Query(default=None),
        limit: int = Query(default=10, ge=1, le=100),
        user: str = Depends(require_user),
    ) -> dict[str, object]:
        results = search_memories(query=q, tags=tag, limit=limit)
        return {"results": results}

    @app.get("/memory/list")
    def memory_list(
        limit: int = Query(default=20, ge=1, le=100),
        user: str = Depends(require_user),
    ) -> dict[str, object]:
        results = list_recent(limit=limit)
        return {"results": results}

    @app.delete("/memory/{memory_id}")
    def memory_delete(memory_id: str, user: str = Depends(require_user)) -> dict[str, bool]:
        deleted = delete_memory(memory_id)
        return {"deleted": deleted}

    @app.post("/finance/accounts")
    def finance_account_upsert(payload: FinanceAccountRequest, user: str = Depends(require_user)) -> dict[str, object]:
        _ = user
        return upsert_account(**payload.model_dump())

    @app.post("/finance/add")
    def finance_add(payload: FinanceAddRequest, user: str = Depends(require_user)) -> dict[str, str]:
        transaction_id = add_transaction(
            amount_cents=payload.amount_cents,
            currency=payload.currency,
            category=payload.category or "uncategorized",
            merchant=payload.merchant,
            note=payload.note,
            method=payload.method,
            source=user,
            account_id=payload.account_id,
            ts=payload.transaction_date.isoformat(),
        )
        return {"id": transaction_id}

    @app.get("/finance/transactions/{transaction_id}")
    def finance_get_transaction(transaction_id: str, user: str = Depends(require_user)) -> dict[str, object]:
        _ = user
        return {"transaction": get_transaction(transaction_id)}

    @app.patch("/finance/transactions/{transaction_id}")
    def finance_update_transaction(
        transaction_id: str,
        payload: FinanceUpdateRequest,
        user: str = Depends(require_user),
    ) -> dict[str, object]:
        _ = user
        return {"transaction": update_transaction(transaction_id, **payload.model_dump(exclude_unset=True))}

    @app.delete("/finance/transactions/{transaction_id}")
    def finance_delete_transaction(transaction_id: str, user: str = Depends(require_user)) -> dict[str, object]:
        _ = user
        return delete_transaction(transaction_id)

    @app.get("/finance/list")
    def finance_list(
        category: str | None = Query(default=None),
        account_id: str | None = Query(default=None),
        date_from: str | None = Query(default=None),
        date_to: str | None = Query(default=None),
        limit: int = Query(default=50, ge=1, le=200),
        user: str = Depends(require_user),
    ) -> dict[str, object]:
        _ = user
        results = list_transactions(start_ts=date_from, end_ts=date_to, category=category, account_id=account_id, limit=limit)
        return {"results": results}

    @app.get("/finance/summary")
    def finance_summary(
        period: str = Query(default="week"),
        start_ts: str | None = Query(default=None),
        end_ts: str | None = Query(default=None),
        account_id: str | None = Query(default=None),
        user: str = Depends(require_user),
    ) -> dict[str, object]:
        _ = user
        report = summary(period=period, start_ts=start_ts, end_ts=end_ts, group_by="category")
        if period == "custom" and start_ts and end_ts:
            spending = spending_summary(start_ts[:10], end_ts[:10], account_id=account_id)
            categories = category_summary(start_ts[:10], end_ts[:10], account_id=account_id)
            return {"report": report, "spending": spending, "categories": categories}
        return {"report": report}

    @app.get("/finance/spending-summary")
    def finance_spending_summary(
        date_from: str = Query(...),
        date_to: str = Query(...),
        account_id: str | None = Query(default=None),
        user: str = Depends(require_user),
    ) -> dict[str, object]:
        _ = user
        request = SpendingSummaryRequest(date_from=date_from, date_to=date_to, account_id=account_id)
        return {"summary": spending_summary(request.date_from.isoformat(), request.date_to.isoformat(), request.account_id)}

    @app.get("/finance/category-summary")
    def finance_category_summary(
        date_from: str = Query(...),
        date_to: str = Query(...),
        account_id: str | None = Query(default=None),
        user: str = Depends(require_user),
    ) -> dict[str, object]:
        _ = user
        request = SpendingSummaryRequest(date_from=date_from, date_to=date_to, account_id=account_id)
        return {"summary": category_summary(request.date_from.isoformat(), request.date_to.isoformat(), request.account_id)}

    @app.post("/finance/intelligence/brief")
    def finance_intelligence_brief(
        payload: FinanceBriefRequest = Body(default_factory=FinanceBriefRequest),
        user: str = Depends(require_user),
    ) -> dict[str, object]:
        transactions = list_transactions(limit=300)
        snapshot = {
            "transactions": transactions,
            "summary": summary(period="month", group_by="category"),
            "cards": payload.cards,
            "budget": payload.budget,
            "savings_goals": payload.savings_goals,
            "holdings": payload.holdings,
            "watchlist": payload.watchlist,
            "paycheck_days": payload.paycheck_days or [],
        }
        return generate_finance_brief(snapshot)

    @app.get("/finance/alerts")
    def finance_alerts(
        limit: int = Query(default=100, ge=1, le=500),
        user: str = Depends(require_user),
    ) -> dict[str, object]:
        return {"alerts": list_alerts(limit=limit)}

    @app.get("/finance/behavior")
    def finance_behavior(
        limit: int = Query(default=100, ge=1, le=500),
        user: str = Depends(require_user),
    ) -> dict[str, object]:
        return {"behavior_logs": list_behavior_logs(limit=limit)}

    @app.get("/finance/rules")
    def finance_rules(user: str = Depends(require_user)) -> dict[str, object]:
        return {"rules": get_rule_thresholds()}

    @app.post("/finance/rules")
    def finance_rules_update(payload: FinanceRuleUpdateRequest, user: str = Depends(require_user)) -> dict[str, object]:
        updated = set_rule_threshold(payload.rule_key, payload.threshold_value, payload.enabled)
        return {"rule": updated}

    @app.get("/files/list")
    def files_list(user: str = Depends(require_user)) -> dict[str, object]:
        files = list_sandbox_files()
        return {"files": files}

    @app.get("/files/read")
    def files_read(path: str = Query(...), user: str = Depends(require_user)) -> dict[str, object]:
        try:
            content = read_sandbox_file(path)
        except FileSandboxError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=VictusError(str(exc)).user_message()) from exc
        return {"content": content}

    @app.post("/files/write")
    def files_write(payload: FileWriteRequest, user: str = Depends(require_user)) -> dict[str, bool]:
        try:
            write_sandbox_file(payload.path, payload.content, payload.mode)
        except FileSandboxError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=VictusError(str(exc)).user_message()) from exc
        return {"ok": True}

    @app.get("/camera/status", response_model=CameraStatus)
    def camera_status(request: Request, user: str = Depends(require_user)) -> CameraStatus:
        request_id = _request_id(request)
        return camera_service.status(request_id=request_id)

    @app.post("/camera/capture", response_model=CaptureResponse)
    def camera_capture(
        request: Request,
        payload: CameraCaptureRequest = Body(default_factory=CameraCaptureRequest),
        user: str = Depends(require_user),
    ) -> CaptureResponse:
        request_id = _request_id(request)
        return camera_service.capture(
            request_id=request_id, reason=payload.reason, format=payload.format
        )

    @app.post("/camera/recognize", response_model=RecognizeResponse)
    def camera_recognize(
        request: Request,
        payload: CameraRecognizeRequest = Body(default_factory=CameraRecognizeRequest),
        user: str = Depends(require_user),
    ) -> RecognizeResponse:
        request_id = _request_id(request)
        return camera_service.recognize(
            request_id=request_id,
            capture_id=payload.capture_id,
            image_b64=payload.image_b64,
        )

    if dist_dir.exists():

        @app.get("/", include_in_schema=False)
        def web_root() -> FileResponse:
            return FileResponse(dist_dir / "index.html")

        app.mount("/", StaticFiles(directory=dist_dir, html=True), name="web")

    return app


app = create_app()
