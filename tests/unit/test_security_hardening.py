from __future__ import annotations

import pytest

from core.config import get_security_config
from core.errors import VictusError
from core.logging.logger import redact_fields
from core.memory.service import MemoryService
from core.orchestrator.router import _TOOL_REGISTRY, _execute_intent
from core.orchestrator.schemas import Intent


class _FakeRepo:
    def __init__(self) -> None:
        self.items: list[dict[str, object]] = []

    def add_memory(self, record: dict[str, object]) -> str:
        self.items.append(record)
        return str(record["id"])

    def search_memories(self, query: str, tags: list[str] | None, limit: int) -> list[dict[str, object]]:
        _ = query, tags
        return self.items[:limit]

    def list_recent(self, limit: int) -> list[dict[str, object]]:
        return self.items[:limit]

    def get_by_id(self, memory_id: str) -> dict[str, object] | None:
        for item in self.items:
            if item["id"] == memory_id:
                return item
        return None

    def delete_memory(self, memory_id: str) -> bool:
        return memory_id == "ok"


def test_memory_service_defaults_sensitivity_and_filters() -> None:
    repo = _FakeRepo()
    service = MemoryService(repository=repo)  # type: ignore[arg-type]

    service.write({"content": "internal note"})
    service.write({"content": "critical note", "sensitivity": "critical"})

    all_default = service.retrieve("", max_items=10)
    assert len(all_default) == 1
    assert all_default[0]["sensitivity"] == "internal"

    allowed_critical = service.retrieve("", max_items=10, allowed_sensitivity=["critical"])
    assert len(allowed_critical) == 2




def test_unknown_sensitivity_rejected() -> None:
    repo = _FakeRepo()
    service = MemoryService(repository=repo)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="Unsupported sensitivity"):
        service.write({"content": "secret", "sensitivity": "top-secret"})


def test_prod_forces_redaction_even_if_disabled(monkeypatch) -> None:
    monkeypatch.setenv("VICTUS_ENV", "prod")
    monkeypatch.setenv("VICTUS_LOG_REDACTION_ENABLED", "false")

    assert get_security_config().log_redaction_enabled is True


def test_tool_registry_blocks_action_missing_handler_even_if_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VICTUS_ENABLED_TOOLS", "noop")
    monkeypatch.delitem(_TOOL_REGISTRY, "noop", raising=False)

    message, actions = _execute_intent(Intent(action="noop", parameters={}, confidence=1.0))
    assert message == "No action executed."
    assert actions == []

def test_redaction_rules_cover_fields_and_patterns() -> None:
    jwt_like = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhZG1pbiI6dHJ1ZX0.c2lnbmF0dXJl"
    payload = redact_fields(
        {
            "api_key": "sk-1234567890123456789012345",
            "headers": "Authorization: Bearer abc.def.ghi",
            "note": f"embedded token {jwt_like}",
            "nested": {"password": "letmein"},
        },
        enabled=True,
    )
    assert payload["api_key"] == "[REDACTED]"
    assert "[REDACTED]" in str(payload["headers"])
    assert "[REDACTED]" in str(payload["note"])
    assert payload["nested"]["password"] == "[REDACTED]"


def test_tool_registry_blocks_unknown_tool() -> None:
    message, actions = _execute_intent(Intent(action="unknown.action", parameters={}, confidence=1.0))
    assert message == "No action executed."
    assert actions == []


def test_error_sanitization_dev_vs_prod(monkeypatch) -> None:
    monkeypatch.setenv("VICTUS_ENV", "dev")
    assert VictusError("low-level detail").user_message() == "low-level detail"

    monkeypatch.setenv("VICTUS_ENV", "prod")
    assert VictusError("low-level detail").user_message() == "The request could not be completed safely."
