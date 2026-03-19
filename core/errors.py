from __future__ import annotations

from dataclasses import dataclass

from core.config import get_security_config


@dataclass
class VictusError(Exception):
    message: str
    safe_message: str = "The request could not be completed safely."
    code: str = "request_failed"

    def user_message(self) -> str:
        config = get_security_config()
        if config.env == "dev":
            return self.message
        return self.safe_message

    def to_response(self) -> dict[str, str]:
        return {"error": self.code, "message": self.user_message()}



def sanitize_exception(exc: Exception) -> VictusError:
    if isinstance(exc, VictusError):
        return exc
    return VictusError(message=str(exc))
