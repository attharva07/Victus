from __future__ import annotations

from typing import Any


def list_threads_handler(parameters: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    _ = parameters, context
    return {
        "threads": [],
        "integration_status": "not_configured",
        "message": "Mail integration is not yet wired for this environment.",
    }


def summarize_thread_handler(parameters: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    _ = context
    thread_id = parameters.get("thread_id")
    if not isinstance(thread_id, str) or not thread_id.strip():
        raise ValueError("'thread_id' is required")
    return {
        "thread_id": thread_id,
        "summary": None,
        "integration_status": "not_configured",
        "message": "Mail integration is not yet wired for this environment.",
    }
