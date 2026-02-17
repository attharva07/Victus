from __future__ import annotations

import time
import uuid
from pathlib import Path

from fastapi import HTTPException, status

from victus.ui_state.models import UIState
from victus.ui_state.store import connection_for_writes, fetch_ui_state


def _event_id() -> str:
    return f"timeline-{uuid.uuid4().hex}"


def _message_id() -> str:
    return f"dialogue-{uuid.uuid4().hex}"


def _require_rowcount(updated: int, entity: str, entity_id: str) -> None:
    if updated <= 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": f"{entity} '{entity_id}' was not found."},
        )


def approval_decision(approval_id: str, decision: str, db_path: Path | None = None) -> UIState:
    now = int(time.time() * 1000)
    with connection_for_writes(db_path) as conn:
        row = conn.execute("SELECT title FROM entities WHERE id = ? AND kind = 'approval'", (approval_id,)).fetchone()
        if row is None:
            _require_rowcount(0, "approval", approval_id)

        conn.execute("DELETE FROM entities WHERE id = ? AND kind = 'approval'", (approval_id,))
        conn.execute(
            "INSERT INTO timeline_events (id, label, detail, created_at) VALUES (?, ?, ?, ?)",
            (_event_id(), f"Approval resolved: {row['title']} ({decision})", f"Approval {decision} by operator.", now),
        )
        conn.commit()
    return fetch_ui_state(db_path)


def mark_reminder_done(reminder_id: str, db_path: Path | None = None) -> UIState:
    now = int(time.time() * 1000)
    with connection_for_writes(db_path) as conn:
        row = conn.execute("SELECT title FROM entities WHERE id = ? AND kind = 'reminder'", (reminder_id,)).fetchone()
        if row is None:
            _require_rowcount(0, "reminder", reminder_id)

        conn.execute("DELETE FROM entities WHERE id = ? AND kind = 'reminder'", (reminder_id,))
        conn.execute(
            "INSERT INTO timeline_events (id, label, detail, created_at) VALUES (?, ?, ?, ?)",
            (_event_id(), f"Done: {row['title']}", "Item marked done and removed from adaptive lanes.", now),
        )
        conn.commit()
    return fetch_ui_state(db_path)


def workflow_action(workflow_id: str, action: str, db_path: Path | None = None) -> UIState:
    now = int(time.time() * 1000)
    with connection_for_writes(db_path) as conn:
        row = conn.execute(
            "SELECT title, status, progress, step, total_steps FROM entities WHERE id = ? AND kind = 'workflow'",
            (workflow_id,),
        ).fetchone()
        if row is None:
            _require_rowcount(0, "workflow", workflow_id)

        status_value = row["status"]
        progress = int(row["progress"] or 0)
        step = int(row["step"] or 1)
        total_steps = int(row["total_steps"] or 1)

        if action == "resume":
            status_value = "active"
            progress = min(100, progress + 10)
        elif action == "pause":
            status_value = "paused"
        elif action == "advance_step":
            step = min(total_steps, step + 1)
            progress = min(100, int((step / max(total_steps, 1)) * 100))
            status_value = "completed" if step >= total_steps else "active"
        else:
            raise HTTPException(status_code=400, detail={"error": "invalid_action", "message": "Unsupported workflow action."})

        detail = f"Step {step}/{total_steps} · {progress}%"
        conn.execute(
            """
            UPDATE entities
            SET status = ?, progress = ?, step = ?, detail = ?, updated_at = ?
            WHERE id = ? AND kind = 'workflow'
            """,
            (status_value, progress, step, detail, now, workflow_id),
        )
        conn.execute(
            "INSERT INTO timeline_events (id, label, detail, created_at) VALUES (?, ?, ?, ?)",
            (_event_id(), f"Workflow action: {row['title']}", f"Action '{action}' applied.", now),
        )
        conn.commit()
    return fetch_ui_state(db_path)


def dialogue_send(message: str, db_path: Path | None = None) -> UIState:
    now = int(time.time() * 1000)
    text = message.strip()
    if not text:
        raise HTTPException(status_code=400, detail={"error": "invalid_message", "message": "Message cannot be empty."})

    with connection_for_writes(db_path) as conn:
        conn.execute(
            "INSERT INTO dialogue_messages (id, role, text, created_at) VALUES (?, ?, ?, ?)",
            (_message_id(), "user", text, now),
        )
        conn.execute(
            "INSERT INTO dialogue_messages (id, role, text, created_at) VALUES (?, ?, ?, ?)",
            (_message_id(), "system", "Acknowledged. Command received in local mode.", now + 1),
        )
        conn.execute(
            "INSERT INTO timeline_events (id, label, detail, created_at) VALUES (?, ?, ?, ?)",
            (_event_id(), "Command received", text, now),
        )
        conn.commit()
    return fetch_ui_state(db_path)
