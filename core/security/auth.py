from __future__ import annotations

import base64
import json
import secrets
import time
from dataclasses import dataclass
from typing import Any, Optional

import bcrypt
from fastapi import Depends, HTTPException, Request, status

from core.logging.audit import audit_event
from core.security.bootstrap_store import get_jwt_secret, is_bootstrapped, verify_admin_password


@dataclass(frozen=True)
class TokenPayload:
    sub: str
    iat: int
    exp: int


def authenticate(username: str, password: str) -> bool:
    if not is_bootstrapped():
        return False
    return username == "admin" and verify_admin_password(password)


def _encode_payload(payload: TokenPayload, secret: str) -> str:
    payload_json = json.dumps(payload.__dict__).encode("utf-8")
    payload_b64 = base64.urlsafe_b64encode(payload_json).rstrip(b"=").decode("utf-8")
    signature = bcrypt.kdf(
        password=payload_b64.encode("utf-8"),
        salt=secret.encode("utf-8"),
        desired_key_bytes=32,
        rounds=64,
    )
    signature_b64 = base64.urlsafe_b64encode(signature).rstrip(b"=").decode("utf-8")
    return f"{payload_b64}.{signature_b64}"


def _decode_payload(token: str, secret: str) -> Optional[TokenPayload]:
    try:
        payload_b64, signature_b64 = token.split(".", 1)
    except ValueError:
        return None
    expected_signature = bcrypt.kdf(
        password=payload_b64.encode("utf-8"),
        salt=secret.encode("utf-8"),
        desired_key_bytes=32,
        rounds=64,
    )
    expected_b64 = base64.urlsafe_b64encode(expected_signature).rstrip(b"=").decode("utf-8")
    if not secrets.compare_digest(expected_b64, signature_b64):
        return None
    padded = payload_b64 + "=" * (-len(payload_b64) % 4)
    payload_raw = base64.urlsafe_b64decode(padded.encode("utf-8"))
    data = json.loads(payload_raw)
    return TokenPayload(sub=data["sub"], iat=data["iat"], exp=data["exp"])


def create_token(username: str, expires_in: int = 3600) -> str:
    now = int(time.time())
    payload = TokenPayload(sub=username, iat=now, exp=now + expires_in)
    secret = get_jwt_secret()
    return _encode_payload(payload, secret)


def verify_token(token: str) -> Optional[TokenPayload]:
    if not is_bootstrapped():
        return None
    secret = get_jwt_secret()
    payload = _decode_payload(token, secret)
    if payload is None:
        return None
    if payload.exp < int(time.time()):
        return None
    return payload


def get_current_user(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    token = auth_header.split(" ", 1)[1].strip()
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return payload.sub


def require_user(user: str = Depends(get_current_user)) -> str:
    return user


def login_user(username: str, password: str) -> str:
    if not is_bootstrapped():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "not_bootstrapped",
                "message": "Run `python -m apps.local.bootstrap` to initialize Victus Local.",
            },
        )
    if not authenticate(username, password):
        audit_event("auth_failed", username=username)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    audit_event("auth_success", username=username)
    return create_token(username)
