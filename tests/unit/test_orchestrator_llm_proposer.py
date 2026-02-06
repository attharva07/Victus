from __future__ import annotations

from pathlib import Path

import io
import json
from urllib import error

import pytest

from adapters.llm.provider import LLMProposer, ProposalResult
from core.config import ensure_directories
from core.orchestrator.router import route_intent
from core.orchestrator.schemas import OrchestrateErrorResponse, OrchestrateRequest, OrchestrateResponse


class _NoopProposer(LLMProposer):
    def propose(self, text: str, domain: str | None, candidates: list[str], context: dict) -> ProposalResult:
        _ = (text, domain, candidates, context)
        return ProposalResult(ok=False, confidence=0.0, reason="none")


class _StaticProposer(LLMProposer):
    def __init__(self, result: ProposalResult):
        self._result = result

    def propose(self, text: str, domain: str | None, candidates: list[str], context: dict) -> ProposalResult:
        _ = (text, domain, candidates, context)
        return self._result


def test_deterministic_still_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VICTUS_LLM_ENABLED", "true")
    response = route_intent(OrchestrateRequest(text="list files"), _NoopProposer())
    assert isinstance(response, OrchestrateResponse)
    assert response.mode == "deterministic"
    assert response.intent.action == "files.list"


def test_unknown_intent_unchanged_when_llm_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VICTUS_LLM_ENABLED", raising=False)
    monkeypatch.delenv("VICTUS_ENABLE_LLM_FALLBACK", raising=False)
    response = route_intent(OrchestrateRequest(text="compute the moon phase please now"), _NoopProposer())
    assert isinstance(response, OrchestrateErrorResponse)
    assert response.error == "unknown_intent"


def test_llm_proposal_returned_not_executed_by_default(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("VICTUS_LLM_ENABLED", "true")
    monkeypatch.setenv("VICTUS_LLM_ALLOW_AUTOEXEC", "false")
    ensure_directories()
    proposer = _StaticProposer(
        ProposalResult(
            ok=True,
            confidence=0.95,
            action="memory.add",
            args={"content": "buy oats"},
            reason="parsed user reminder",
        )
    )
    response = route_intent(OrchestrateRequest(text="please stash this detail"), proposer)
    assert response.mode == "llm_proposal"
    assert response.proposed_action is not None
    assert response.executed is False
    assert response.actions == []


def test_llm_autoexec_only_when_enabled_and_safe(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("VICTUS_LLM_ENABLED", "true")
    monkeypatch.setenv("VICTUS_LLM_ALLOW_AUTOEXEC", "true")
    monkeypatch.setenv("VICTUS_LLM_AUTOEXEC_MIN_CONFIDENCE", "0.90")
    ensure_directories()

    proposer = _StaticProposer(
        ProposalResult(
            ok=True,
            confidence=0.96,
            action="memory.add",
            args={"content": "book dentist"},
            reason="clear memory add request",
        )
    )
    response = route_intent(OrchestrateRequest(text="capture this note"), proposer)
    assert response.mode == "llm_proposal"
    assert response.executed is True
    assert response.intent.action == "memory.add"
    assert response.actions


def test_disallowed_proposal_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VICTUS_LLM_ENABLED", "true")
    proposer = _StaticProposer(
        ProposalResult(
            ok=True,
            confidence=0.99,
            action="system.shell",
            args={"command": "rm -rf /"},
            reason="bad action",
        )
    )
    response = route_intent(OrchestrateRequest(text="do something dangerous now"), proposer)
    assert isinstance(response, OrchestrateErrorResponse)
    assert response.error == "unknown_intent"


class _MockHTTPResponse:
    def __init__(self, payload: dict[str, object]):
        self._buffer = io.BytesIO(json.dumps(payload).encode("utf-8"))

    def read(self) -> bytes:
        return self._buffer.read()

    def __enter__(self) -> "_MockHTTPResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        _ = (exc_type, exc, tb)


def test_ollama_provider_unreachable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VICTUS_LLM_ENABLED", "true")
    monkeypatch.setenv("VICTUS_LLM_PROVIDER", "ollama")

    def _raise_unreachable(*args, **kwargs):
        _ = (args, kwargs)
        raise error.URLError("connection refused")

    monkeypatch.setattr("adapters.llm.provider.request.urlopen", _raise_unreachable)
    proposer = LLMProposer()
    result = proposer.propose(
        text="find my dark mode memory",
        domain=None,
        candidates=["memory.search"],
        context={},
    )
    assert result.ok is False
    assert result.reason == "ollama_unreachable"


def test_ollama_provider_success_returns_llm_proposal(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VICTUS_LLM_ENABLED", "true")
    monkeypatch.setenv("VICTUS_LLM_PROVIDER", "ollama")
    monkeypatch.setenv("VICTUS_LLM_ALLOW_AUTOEXEC", "false")

    ollama_response = {
        "response": json.dumps(
            {
                "ok": True,
                "confidence": 0.93,
                "action": "memory.search",
                "args": {"query": "dark mode", "limit": 5},
                "reason": "mapped to memory search",
                "raw": None,
            }
        )
    }

    def _mock_urlopen(*args, **kwargs):
        _ = (args, kwargs)
        return _MockHTTPResponse(ollama_response)

    monkeypatch.setattr("adapters.llm.provider.request.urlopen", _mock_urlopen)

    response = route_intent(OrchestrateRequest(text="can you find my memory about dark mode"), LLMProposer())
    assert isinstance(response, OrchestrateResponse)
    assert response.mode == "llm_proposal"
    assert response.executed is False
    assert response.proposed_action is not None
    assert response.proposed_action["action"] == "memory.search"
