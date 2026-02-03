from __future__ import annotations

import base64
import hmac
import json
import os
import time
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Optional

import bcrypt
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.config import get_data_dir

AUTH_FILE = "auth.json"
TOKEN_TTL_SECONDS = 60 * 60 * 12


@dataclass
class AuthUser:
    username: str
    role: str


class AuthManager:
    def __init__(self, data_dir: Optional[Path] = None) -> None:
        self.data_dir = data_dir or get_data_dir()
        self.auth_path = self.data_dir / AUTH_FILE
        self._config = self._load_or_create()

    def _load_or_create(self) -> dict[str, str]:
        if self.auth_path.exists():
            return json.loads(self.auth_path.read_text())

        admin_password = os.getenv("VICTUS_ADMIN_PASSWORD", "admin")
        password_hash = bcrypt.hashpw(admin_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        secret_key = base64.urlsafe_b64encode(os.urandom(32)).decode("utf-8")
        config = {
            "username": "admin",
            "role": "admin",
            "password_hash": password_hash,
            "secret_key": secret_key,
        }
        self.auth_path.write_text(json.dumps(config, indent=2))
        return config

    def verify_password(self, username: str, password: str) -> AuthUser:
        if username != self._config.get("username"):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        stored_hash = self._config.get("password_hash", "").encode("utf-8")
        if not bcrypt.checkpw(password.encode("utf-8"), stored_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        return AuthUser(username=username, role=self._config.get("role", "user"))

    def create_token(self, user: AuthUser) -> str:
        payload = {
            "sub": user.username,
            "role": user.role,
            "exp": int(time.time()) + TOKEN_TTL_SECONDS,
        }
        payload_bytes = json.dumps(payload).encode("utf-8")
        encoded_payload = base64.urlsafe_b64encode(payload_bytes).decode("utf-8")
        signature = self._sign(encoded_payload)
        return f"{encoded_payload}.{signature}"

    def verify_token(self, token: str) -> AuthUser:
        try:
            encoded_payload, signature = token.split(".", 1)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

        if not hmac.compare_digest(signature, self._sign(encoded_payload)):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        payload = json.loads(base64.urlsafe_b64decode(encoded_payload.encode("utf-8")))
        if payload.get("exp", 0) < int(time.time()):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")

        return AuthUser(username=payload.get("sub", ""), role=payload.get("role", "user"))

    def _sign(self, encoded_payload: str) -> str:
        secret_key = self._config.get("secret_key", "")
        digest = hmac.new(secret_key.encode("utf-8"), encoded_payload.encode("utf-8"), sha256).digest()
        return base64.urlsafe_b64encode(digest).decode("utf-8")


security_scheme = HTTPBearer(auto_error=False)


def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = None) -> AuthUser:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    manager = AuthManager()
    return manager.verify_token(credentials.credentials)
