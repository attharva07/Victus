from __future__ import annotations

import logging
import time
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials

from core.config import get_data_dir
from core.logging.logger import setup_logging
from core.logging.audit import AuditEvent, log_event
from core.orchestrator.router import orchestrate
from core.orchestrator.schemas import OrchestrateRequest, OrchestrateResponse
from core.security.auth import AuthManager, AuthUser, get_current_user, security_scheme

logger = logging.getLogger("victus.local")

app = FastAPI(title="Victus Local")


@app.on_event("startup")
async def configure_logging() -> None:
    setup_logging()


@app.middleware("http")
async def request_logger(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = int((time.time() - start) * 1000)

    headers = {k.lower(): v for k, v in request.headers.items()}
    headers.pop("authorization", None)
    headers.pop("cookie", None)

    logger.info(
        "request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": duration_ms,
            "headers": headers,
        },
    )
    return response


@app.get("/health")
async def health() -> dict[str, str]:
    get_data_dir()
    return {"status": "ok"}


@app.post("/login")
async def login(payload: dict[str, str]) -> dict[str, str]:
    username = payload.get("username")
    password = payload.get("password")
    if not username or not password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing credentials")
    manager = AuthManager()
    user = manager.verify_password(username, password)
    token = manager.create_token(user)
    log_event(
        AuditEvent(
            event_type="login",
            actor=user.username,
            resource="/login",
            result="success",
        )
    )
    return {"token": token}


@app.get("/me")
async def me(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)) -> dict[str, str]:
    user = get_current_user(credentials)
    return {"username": user.username, "role": user.role}


@app.post("/orchestrate", response_model=OrchestrateResponse)
async def orchestrate_endpoint(
    request: OrchestrateRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> OrchestrateResponse:
    user: AuthUser = get_current_user(credentials)
    intent, message = orchestrate(request.text, actor=user.username, role=user.role)
    return OrchestrateResponse(intent=intent, actions_taken=[], message=message)
