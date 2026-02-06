from __future__ import annotations

import json
import os
from urllib import error, request
from typing import Any

from pydantic import BaseModel, Field


class ProposalResult(BaseModel):
    ok: bool = False
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    action: str | None = None
    args: dict[str, Any] = Field(default_factory=dict)
    reason: str = "llm_proposer_stub"
    raw: dict[str, Any] | None = None


class LLMProposer:
    def propose(
        self,
        text: str,
        domain: str | None,
        candidates: list[str],
        context: dict[str, Any],
    ) -> ProposalResult:
        config = _get_llm_config()
        if not config["enabled"]:
            return ProposalResult(ok=False, confidence=0.0, reason="llm_disabled")

        provider = config["provider"]
        if provider == "stub":
            return ProposalResult(ok=False, confidence=0.0, reason="provider_stub")
        if provider == "ollama":
            return _propose_with_ollama(
                text=text,
                domain=domain,
                candidates=candidates,
                context=context,
                base_url=config["ollama_base_url"],
                model=config["model"],
            )
        return ProposalResult(ok=False, confidence=0.0, reason="provider_unknown")


class StubLLMProposer(LLMProposer):
    pass


# Backwards-compatible alias used by existing imports.
class LLMProvider(StubLLMProposer):
    def propose_intent(self, request: Any) -> None:
        _ = request
        return None


def _get_llm_config() -> dict[str, Any]:
    llm_enabled = os.getenv("VICTUS_LLM_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
    legacy_fallback = os.getenv("VICTUS_ENABLE_LLM_FALLBACK", "false").strip().lower() in {"1", "true", "yes", "on"}
    enabled = llm_enabled or legacy_fallback
    provider = os.getenv("VICTUS_LLM_PROVIDER", "stub").strip().lower() or "stub"
    ollama_base_url = os.getenv("VICTUS_OLLAMA_BASE_URL", "http://127.0.0.1:11434").strip() or "http://127.0.0.1:11434"
    model = os.getenv("VICTUS_LLM_MODEL", "llama3.1:latest").strip() or "llama3.1:latest"
    return {
        "enabled": enabled,
        "provider": provider,
        "ollama_base_url": ollama_base_url,
        "model": model,
    }


def _proposal_prompt(text: str, domain: str | None, candidates: list[str], context: dict[str, Any]) -> str:
    payload = {
        "text": text,
        "domain": domain,
        "candidates": candidates,
        "context": context,
    }
    return (
        "You are an intent proposer for a deterministic orchestrator.\n"
        "Choose only from candidates.\n"
        "Return STRICT JSON only, no markdown or prose, matching this object shape exactly:\n"
        '{"ok":bool,"confidence":number,"action":string|null,"args":object,"reason":string,"raw":object|null}\n'
        "If unsure, return {\"ok\":false,\"confidence\":0.0,\"action\":null,\"args\":{},\"reason\":\"uncertain\",\"raw\":null}.\n"
        f"Request payload: {json.dumps(payload, ensure_ascii=False)}"
    )


def _propose_with_ollama(
    text: str,
    domain: str | None,
    candidates: list[str],
    context: dict[str, Any],
    base_url: str,
    model: str,
) -> ProposalResult:
    endpoint = f"{base_url.rstrip('/')}/api/generate"
    request_payload = {
        "model": model,
        "prompt": _proposal_prompt(text=text, domain=domain, candidates=candidates, context=context),
        "stream": False,
        "format": "json",
    }
    body = json.dumps(request_payload).encode("utf-8")
    http_request = request.Request(endpoint, data=body, headers={"Content-Type": "application/json"}, method="POST")

    try:
        with request.urlopen(http_request, timeout=10) as response:
            response_bytes = response.read()
    except error.URLError:
        return ProposalResult(ok=False, confidence=0.0, reason="ollama_unreachable")
    except TimeoutError:
        return ProposalResult(ok=False, confidence=0.0, reason="ollama_unreachable")
    except Exception:
        return ProposalResult(ok=False, confidence=0.0, reason="ollama_unreachable")

    try:
        ollama_payload = json.loads(response_bytes.decode("utf-8"))
        raw_text = ollama_payload.get("response", "")
        proposal_payload = json.loads(raw_text)
    except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
        return ProposalResult(ok=False, confidence=0.0, reason="ollama_invalid_json")

    if not isinstance(proposal_payload, dict):
        return ProposalResult(ok=False, confidence=0.0, reason="ollama_invalid_json", raw={"payload": proposal_payload})

    try:
        proposal = ProposalResult.model_validate(proposal_payload)
    except Exception:
        return ProposalResult(ok=False, confidence=0.0, reason="ollama_invalid_json", raw={"payload": proposal_payload})

    proposal.raw = ollama_payload
    return proposal
