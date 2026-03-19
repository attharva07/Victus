from __future__ import annotations

import json
import os
from typing import Any
from urllib import error, request

from pydantic import BaseModel, Field


class ProposalResult(BaseModel):
    ok: bool = False
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    action: str | None = None
    args: dict[str, Any] = Field(default_factory=dict)
    reason: str = "llm_proposer_stub"
    raw: dict[str, Any] | None = None
    selected_model: str | None = None
    llm_used: bool = False
    clarify_question: str | None = None


class LLMProposer:
    def __init__(self) -> None:
        self._last_error: str | None = None
        self._selected_model: str | None = None

    def propose(
        self,
        text: str,
        domain: str | None,
        candidates: list[str],
        context: dict[str, Any],
    ) -> ProposalResult:
        config = _get_llm_config()
        if not config["enabled"]:
            self._last_error = "llm_disabled"
            return ProposalResult(ok=False, confidence=0.0, reason="llm_disabled")

        provider = config["provider"]
        if provider == "stub":
            self._last_error = "provider_stub"
            return ProposalResult(ok=False, confidence=0.0, reason="provider_stub")
        if provider == "ollama":
            return _propose_with_ollama(
                text=text,
                domain=domain,
                candidates=candidates,
                context=context,
                base_url=config["ollama_base_url"],
                model_priority=config["model_priority"],
                configured_model=config["configured_model"],
                on_error=self._set_error,
                on_selected_model=self._set_selected_model,
            )
        self._last_error = "provider_unknown"
        return ProposalResult(ok=False, confidence=0.0, reason="provider_unknown")

    def _set_error(self, error_text: str) -> None:
        self._last_error = error_text

    def _set_selected_model(self, model: str | None) -> None:
        self._selected_model = model

    def debug_status(self, *, llm_enabled: bool = False) -> dict[str, Any]:
        config = _get_llm_config()
        return {
            "llm_enabled": llm_enabled or config["enabled"],
            "provider": config["provider"],
            "selected_model": self._selected_model,
            "model_priority": config["model_priority"],
            "last_error": self._last_error,
        }


class StubLLMProposer(LLMProposer):
    pass


# Backwards-compatible alias used by existing imports.
class LLMProvider(StubLLMProposer):
    def propose_intent(self, request: Any) -> None:
        _ = request
        return None


def _get_llm_config() -> dict[str, Any]:
    llm_enabled = os.getenv("VICTUS_LLM_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
    legacy_fallback = os.getenv("VICTUS_ENABLE_LLM_FALLBACK", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    enabled = llm_enabled or legacy_fallback
    provider = os.getenv("VICTUS_LLM_PROVIDER", "stub").strip().lower() or "stub"
    ollama_base_url = os.getenv("VICTUS_OLLAMA_BASE_URL", "http://127.0.0.1:11434").strip() or "http://127.0.0.1:11434"
    model_priority_raw = os.getenv("VICTUS_OLLAMA_MODEL_PRIORITY", "mistral,llama3.1:8b")
    model_priority = [entry.strip() for entry in model_priority_raw.split(",") if entry.strip()]
    configured_model = os.getenv("VICTUS_LLM_MODEL", "").strip()
    return {
        "enabled": enabled,
        "provider": provider,
        "ollama_base_url": ollama_base_url,
        "model_priority": model_priority or ["mistral", "llama3.1:8b"],
        "configured_model": configured_model or None,
    }


def _proposal_prompt(text: str, domain: str | None, candidates: list[str], context: dict[str, Any]) -> str:
    payload = {
        "text": text,
        "domain": domain,
        "allowed_actions": candidates,
        "context": context,
    }
    return (
        "You are an intent proposer for a deterministic orchestrator.\n"
        "Return STRICT JSON ONLY (no markdown), using this exact shape:\n"
        '{"action":"<allowed_action>","parameters":{},"confidence":0.0,"clarify_question":"optional"}\n'
        "Allowed actions are exactly: "
        f"{json.dumps(candidates)}\n"
        "If unsure: return action=\"noop\", confidence<=0.4, and include clarify_question.\n"
        f"User request: {json.dumps(payload, ensure_ascii=False)}"
    )


def _repair_prompt(invalid_output: str, candidates: list[str]) -> str:
    return (
        "Repair this invalid JSON into STRICT JSON ONLY matching this shape: "
        '{"action":"<allowed_action>","parameters":{},"confidence":0.0,"clarify_question":"optional"}. '
        f"Allowed actions: {json.dumps(candidates)}. "
        f"Invalid output: {invalid_output}"
    )


def _http_json(url: str, payload: dict[str, Any], timeout: int = 10) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    http_request = request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    with request.urlopen(http_request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _http_get_json(url: str, timeout: int = 5) -> dict[str, Any]:
    http_request = request.Request(url, method="GET")
    with request.urlopen(http_request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _select_ollama_model(base_url: str, model_priority: list[str]) -> tuple[str | None, str | None]:
    try:
        tags = _http_get_json(f"{base_url.rstrip('/')}/api/tags")
    except error.HTTPError as exc:
        if exc.code == 404:
            return None, "ollama_no_model"
        return None, "ollama_unreachable"
    except (error.URLError, TimeoutError):
        return None, "ollama_unreachable"
    except Exception:  # noqa: BLE001
        return None, "ollama_unreachable"

    if not isinstance(tags, dict):
        return (model_priority[0], None) if model_priority else (None, "ollama_no_model")

    raw_models = tags.get("models")
    if not isinstance(raw_models, list):
        return (model_priority[0], None) if model_priority else (None, "ollama_no_model")

    available = {entry.get("name") for entry in raw_models if isinstance(entry, dict) and entry.get("name")}
    for candidate in model_priority:
        if candidate in available:
            return candidate, None
    return None, "ollama_no_model"


def _extract_first_json_object(payload_text: str) -> str | None:
    start = payload_text.find("{")
    if start < 0:
        return None
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(payload_text)):
        char = payload_text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return payload_text[start : index + 1]
    return None


def _parse_intent_payload(payload_text: str) -> tuple[dict[str, Any] | None, str | None]:
    json_blob = _extract_first_json_object(payload_text)
    if json_blob is None:
        return None, "invalid_json"
    try:
        parsed = json.loads(json_blob)
    except json.JSONDecodeError:
        return None, "invalid_json"
    if not isinstance(parsed, dict):
        return None, "invalid_shape"
    return parsed, None


def _propose_with_ollama(
    text: str,
    domain: str | None,
    candidates: list[str],
    context: dict[str, Any],
    base_url: str,
    model_priority: list[str],
    configured_model: str | None,
    on_error: Any,
    on_selected_model: Any,
) -> ProposalResult:
    if configured_model:
        model = configured_model
        model_error = None
    else:
        model, model_error = _select_ollama_model(base_url, model_priority)
    on_selected_model(model)
    if model is None:
        error_reason = model_error or "ollama_no_model"
        on_error(error_reason)
        return ProposalResult(ok=False, confidence=0.0, reason=error_reason)

    endpoint = f"{base_url.rstrip('/')}/api/generate"
    request_payload = {
        "model": model,
        "prompt": _proposal_prompt(text=text, domain=domain, candidates=candidates, context=context),
        "stream": False,
        "format": "json",
    }

    def _run_prompt(prompt_payload: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None, dict[str, Any] | None]:
        try:
            ollama_payload = _http_json(endpoint, prompt_payload, timeout=10)
        except error.HTTPError as exc:
            if exc.code == 404:
                return None, "ollama_no_model", None
            return None, "ollama_unreachable", None
        except (error.URLError, TimeoutError):
            return None, "ollama_unreachable", None
        except Exception:  # noqa: BLE001
            return None, "ollama_unreachable", None
        raw_text = ollama_payload.get("response", "") if isinstance(ollama_payload, dict) else ""
        parsed, parse_error = _parse_intent_payload(raw_text)
        return parsed, parse_error, ollama_payload if isinstance(ollama_payload, dict) else None

    parsed, parse_error, raw_payload = _run_prompt(request_payload)
    if parse_error == "invalid_json":
        repair_payload = {
            "model": model,
            "prompt": _repair_prompt(raw_payload.get("response", "") if raw_payload else "", candidates),
            "stream": False,
            "format": "json",
        }
        parsed, parse_error, raw_payload = _run_prompt(repair_payload)

    if parse_error or parsed is None:
        reason = "ollama_invalid_json" if parse_error == "invalid_json" else (parse_error or "ollama_invalid_json")
        on_error(reason)
        return ProposalResult(ok=False, confidence=0.0, reason=reason, selected_model=model, llm_used=True)

    action = parsed.get("action")
    parameters = parsed.get("parameters")
    if not isinstance(parameters, dict):
        parameters = parsed.get("args", {})
    confidence = parsed.get("confidence", 0.0)
    clarify_question = parsed.get("clarify_question")
    if not isinstance(parameters, dict):
        parameters = {}
    try:
        confidence_value = float(confidence)
    except (TypeError, ValueError):
        confidence_value = 0.0
    confidence_value = max(0.0, min(1.0, confidence_value))

    on_error("")
    return ProposalResult(
        ok=True,
        confidence=confidence_value,
        action=action if isinstance(action, str) else None,
        args=parameters,
        reason="ok",
        raw=raw_payload,
        selected_model=model,
        llm_used=True,
        clarify_question=clarify_question if isinstance(clarify_question, str) else None,
    )
