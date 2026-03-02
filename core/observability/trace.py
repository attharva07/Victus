from __future__ import annotations

import json
import os
import time
import traceback
from collections import OrderedDict
from threading import Lock
from typing import Any
from uuid import uuid4

from core.logging.logger import get_logger

_SECRET_KEYS = {"password", "token", "secret", "api_key", "authorization", "auth"}
_MAX_STRING_LEN = 1024


class TraceStore:
    def __init__(self, capacity: int = 200) -> None:
        self.capacity = capacity
        self._entries: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self._lock = Lock()

    def put(self, trace_id: str, payload: dict[str, Any]) -> None:
        with self._lock:
            if trace_id in self._entries:
                self._entries.pop(trace_id)
            self._entries[trace_id] = payload
            if len(self._entries) > self.capacity:
                self._entries.popitem(last=False)

    def get(self, trace_id: str) -> dict[str, Any] | None:
        with self._lock:
            return self._entries.get(trace_id)


TRACE_STORE = TraceStore(capacity=200)


def is_debug_enabled() -> bool:
    return os.getenv("VICTUS_DEBUG") == "1"


def ensure_trace_id(request_id: str | None) -> str:
    value = (request_id or "").strip()
    return value if value else str(uuid4())


def _redact_string(value: str, key_hint: str | None = None) -> str:
    if key_hint and key_hint.lower() in _SECRET_KEYS:
        return "[REDACTED]"
    lowered = value.lower()
    if any(marker in lowered for marker in ("password", "token", "secret", "api_key", "authorization")):
        return "[REDACTED]"
    if len(value.encode("utf-8")) > _MAX_STRING_LEN:
        return "[REDACTED_LARGE_CONTENT]"
    return value


def redact_payload(payload: Any, *, key_hint: str | None = None) -> Any:
    if isinstance(payload, dict):
        result: dict[str, Any] = {}
        for key, value in payload.items():
            hint = str(key)
            if hint.lower() in _SECRET_KEYS:
                result[key] = "[REDACTED]"
                continue
            result[key] = redact_payload(value, key_hint=hint)
        return result
    if isinstance(payload, list):
        return [redact_payload(item, key_hint=key_hint) for item in payload]
    if isinstance(payload, str):
        return _redact_string(payload, key_hint=key_hint)
    return payload


class StageTimer:
    def __init__(self, tracer: "TraceRecorder", stage: str, *, stage_input: Any = None) -> None:
        self.tracer = tracer
        self.stage = stage
        self.stage_input = stage_input
        self._start = 0.0

    def __enter__(self) -> "StageTimer":
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type: Any, exc: BaseException | None, _tb: Any) -> bool:
        duration_ms = round((time.perf_counter() - self._start) * 1000, 3)
        if exc is None:
            self.tracer.record_stage(self.stage, stage_input=self.stage_input, duration_ms=duration_ms)
            return False
        self.tracer.record_exception(self.stage, exc, stage_input=self.stage_input, duration_ms=duration_ms)
        return False


class TraceRecorder:
    def __init__(self, trace_id: str, *, route: str, debug: bool | None = None) -> None:
        self.trace_id = trace_id
        self.route = route
        self.debug = is_debug_enabled() if debug is None else debug
        self.logger = get_logger()
        self.started_at = time.perf_counter()
        self.stages: list[dict[str, Any]] = []
        self.stage_reached = "request_intake"
        self.unknown_reason: str | None = None

    def timer(self, stage: str, *, stage_input: Any = None) -> StageTimer:
        return StageTimer(self, stage, stage_input=stage_input)

    def record_stage(
        self,
        stage: str,
        *,
        stage_input: Any = None,
        stage_output: Any = None,
        reason: str | None = None,
        duration_ms: float | None = None,
    ) -> None:
        self.stage_reached = stage
        if reason:
            self.unknown_reason = reason
        event = {
            "trace_id": self.trace_id,
            "route": self.route,
            "stage": stage,
            "status": "ok",
            "duration_ms": duration_ms,
            "reason": reason,
            "input": redact_payload(stage_input),
            "output": redact_payload(stage_output),
        }
        self.stages.append(event)
        self.logger.info(json.dumps({"event": "orchestration_stage", **event}))

    def record_exception(
        self,
        stage: str,
        exc: BaseException,
        *,
        stage_input: Any = None,
        duration_ms: float | None = None,
    ) -> None:
        event = {
            "trace_id": self.trace_id,
            "route": self.route,
            "stage": stage,
            "status": "error",
            "duration_ms": duration_ms,
            "input": redact_payload(stage_input),
            "exception": {
                "type": type(exc).__name__,
                "message": str(exc),
                "stack_trace": traceback.format_exc(),
            },
        }
        self.stages.append(event)
        self.logger.exception(json.dumps({"event": "orchestration_exception", **event}))

    def finalize(self, *, response: Any = None, config_flags: dict[str, Any] | None = None) -> dict[str, Any]:
        total_ms = round((time.perf_counter() - self.started_at) * 1000, 3)
        payload = {
            "trace_id": self.trace_id,
            "route": self.route,
            "stage_reached": self.stage_reached,
            "total_latency_ms": total_ms,
            "unknown_reason": self.unknown_reason,
            "stages": self.stages,
            "config_flags": redact_payload(config_flags or {}),
            "response": redact_payload(response),
        }
        TRACE_STORE.put(self.trace_id, payload)
        self.logger.info(json.dumps({"event": "orchestration_complete", **payload}))
        return payload

    def build_debug_payload(self, *, config_flags: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.debug:
            return {}
        return {
            "trace_id": self.trace_id,
            "stage_reached": self.stage_reached,
            "stages": self.stages,
            "config_flags": redact_payload(config_flags or {}),
            "reason": self.unknown_reason,
        }
