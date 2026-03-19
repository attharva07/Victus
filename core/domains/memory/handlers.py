from __future__ import annotations

from typing import Any

from core.memory.service import (
    add_memory,
    delete_memory,
    get_memory_by_id,
    list_recent,
    search_memories,
)


def create_note_handler(parameters: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    content = parameters.get("content")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("'content' is required")
    memory_id = add_memory(
        content=content.strip(),
        type=str(parameters.get("type") or "note"),
        tags=parameters.get("tags") if isinstance(parameters.get("tags"), list) else None,
        source=str(context.get("user_id") or "user"),
        importance=int(parameters.get("importance") or 5),
        confidence=float(parameters.get("confidence") or 0.8),
        sensitivity=parameters.get("sensitivity") if isinstance(parameters.get("sensitivity"), str) else None,
    )
    return {"memory_id": memory_id, "message": "Memory stored."}


def search_handler(parameters: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    _ = context
    query = parameters.get("query")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("'query' is required")
    limit = parameters.get("limit", 10)
    if not isinstance(limit, int):
        raise ValueError("'limit' must be an integer")
    results = search_memories(query=query.strip(), tags=parameters.get("tags"), limit=limit)
    return {"results": results, "count": len(results)}


def list_recent_handler(parameters: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    _ = context
    limit = int(parameters.get("limit") or 20)
    results = list_recent(limit=limit)
    return {"results": results, "count": len(results)}


def get_memory_handler(parameters: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    _ = context
    memory_id = parameters.get("memory_id")
    if not isinstance(memory_id, str) or not memory_id.strip():
        raise ValueError("'memory_id' is required")
    record = get_memory_by_id(memory_id.strip())
    if record is None:
        return {"memory": None, "found": False}
    return {"memory": record, "found": True}


def delete_memory_handler(parameters: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    _ = context
    memory_id = parameters.get("memory_id")
    if not isinstance(memory_id, str) or not memory_id.strip():
        raise ValueError("'memory_id' is required")
    deleted = delete_memory(memory_id.strip())
    return {"deleted": deleted, "memory_id": memory_id.strip()}
