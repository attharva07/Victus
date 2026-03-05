from __future__ import annotations

from collections.abc import Callable
from typing import Any

from core.camera.errors import CameraError
from core.camera.service import CameraService
from core.filesystem.service import list_sandbox_files, read_sandbox_file, write_sandbox_file
from core.finance.service import add_transaction, list_transactions, summary
from core.logging.audit import audit_event, safe_excerpt
from core.memory.service import add_memory, delete_memory, list_recent, search_memories
from core.orchestrator.schemas import ActionResult

ToolHandler = Callable[[dict[str, Any]], tuple[str, ActionResult]]


def _camera_status(params: dict[str, Any]) -> tuple[str, ActionResult]:
    status = CameraService().status()
    return f"Camera status: {status.message}", ActionResult(action="camera.status", parameters=params, result=status.model_dump())


def _camera_capture(params: dict[str, Any]) -> tuple[str, ActionResult]:
    try:
        capture = CameraService().capture()
        return "Captured an image from the camera.", ActionResult(action="camera.capture", parameters=params, result=capture.model_dump())
    except CameraError as exc:
        return str(exc), ActionResult(action="camera.capture", parameters=params, result={"error": str(exc)})


def _camera_recognize(params: dict[str, Any]) -> tuple[str, ActionResult]:
    try:
        rec = CameraService().recognize()
        return f"Recognized {len(rec.matches)} face matches.", ActionResult(action="camera.recognize", parameters=params, result=rec.model_dump())
    except CameraError as exc:
        return str(exc), ActionResult(action="camera.recognize", parameters=params, result={"error": str(exc)})


def _memory_add(params: dict[str, Any]) -> tuple[str, ActionResult]:
    memory_id = add_memory(content=params["content"], tags=params.get("tags"), importance=params.get("importance", 5))
    audit_event("orchestrate_memory_add", memory_id=memory_id)
    return f"Saved memory {memory_id}.", ActionResult(action="memory.add", parameters=params, result={"id": memory_id})


def _memory_search(params: dict[str, Any]) -> tuple[str, ActionResult]:
    results = search_memories(query=params.get("query", ""), tags=params.get("tags"), limit=params.get("limit", 10))
    latest = ""
    if results:
        excerpt = str(results[0].get("content", "")).strip()
        latest = f" Latest: {safe_excerpt(excerpt, max_len=80)}." if excerpt else ""
    return (
        f"Found {len(results)} memories matching '{params.get('query', '')}'.{latest}",
        ActionResult(action="memory.search", parameters=params, result={"results": results}),
    )


def _memory_list(params: dict[str, Any]) -> tuple[str, ActionResult]:
    results = list_recent(limit=params.get("limit", 20))
    return f"Listed {len(results)} memories.", ActionResult(action="memory.list", parameters=params, result={"results": results})


def _memory_delete(params: dict[str, Any]) -> tuple[str, ActionResult]:
    deleted = delete_memory(memory_id=params["id"])
    return ("Memory deleted." if deleted else "Memory not found."), ActionResult(action="memory.delete", parameters=params, result={"deleted": deleted})


def _finance_add(params: dict[str, Any]) -> tuple[str, ActionResult]:
    amount_cents = int(round(float(params["amount"]) * 100))
    tx_id = add_transaction(
        amount_cents=amount_cents,
        currency=params.get("currency", "USD"),
        category=params.get("category", "uncategorized"),
        merchant=params.get("merchant"),
        ts=params.get("occurred_at"),
    )
    return (
        f"Recorded ${amount_cents / 100:.2f} in {params.get('category', 'uncategorized')}.",
        ActionResult(action="finance.add_transaction", parameters=params, result={"id": tx_id, "amount_cents": amount_cents}),
    )


def _finance_list(params: dict[str, Any]) -> tuple[str, ActionResult]:
    results = list_transactions(limit=params.get("limit", 50), category=params.get("category"))
    return f"Listed {len(results)} transactions.", ActionResult(action="finance.list_transactions", parameters=params, result={"results": results})


def _finance_summary(params: dict[str, Any]) -> tuple[str, ActionResult]:
    report = summary(period=params.get("period", "week"), group_by=params.get("group_by", "category"))
    return "Generated finance summary.", ActionResult(action="finance.summary", parameters=params, result={"report": report})


def _files_list(params: dict[str, Any]) -> tuple[str, ActionResult]:
    files = list_sandbox_files()
    return f"Listed {len(files)} sandbox files.", ActionResult(action="files.list", parameters=params, result={"files": files})


def _files_read(params: dict[str, Any]) -> tuple[str, ActionResult]:
    content = read_sandbox_file(params["path"])
    return f"Read {params['path']} ({len(content)} chars).", ActionResult(action="files.read", parameters=params, result={"content": content})


def _files_write(params: dict[str, Any]) -> tuple[str, ActionResult]:
    write_sandbox_file(params["path"], params.get("content", ""), params.get("mode", "overwrite"))
    return f"Wrote {params['path']} using {params.get('mode', 'overwrite')} mode.", ActionResult(action="files.write", parameters=params, result={"ok": True})


TOOL_REGISTRY: dict[str, ToolHandler] = {
    "camera.status": _camera_status,
    "camera.capture": _camera_capture,
    "camera.recognize": _camera_recognize,
    "memory.add": _memory_add,
    "memory.search": _memory_search,
    "memory.list": _memory_list,
    "memory.delete": _memory_delete,
    "finance.add_transaction": _finance_add,
    "finance.list_transactions": _finance_list,
    "finance.summary": _finance_summary,
    "files.list": _files_list,
    "files.read": _files_read,
    "files.write": _files_write,
}
