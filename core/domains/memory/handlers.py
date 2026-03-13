from __future__ import annotations

from typing import Any

from core.memory.service import add_memory, search_memories


def create_note_handler(parameters: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    content = parameters.get("content")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("'content' is required")
    memory_id = add_memory(
        content=content.strip(),
        type="note",
        tags=parameters.get("tags") if isinstance(parameters.get("tags"), list) else None,
        source=str(context.get("user_id") or "user"),
        sensitivity=parameters.get("sensitivity") if isinstance(parameters.get("sensitivity"), str) else None,
    )
    return {"memory_id": memory_id, "message": "Note created."}


def search_handler(parameters: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    _ = context
    query = parameters.get("query")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("'query' is required")
    limit = parameters.get("limit", 10)
    if not isinstance(limit, int):
        raise ValueError("'limit' must be an integer")
    results = search_memories(query=query, tags=parameters.get("tags"), limit=limit)
    return {"results": results, "count": len(results)}
