from __future__ import annotations

import sqlite3
import time
import uuid
from pathlib import Path

from platformdirs import user_data_dir

from victus.ui_state.models import UIState

_DB_INITIALIZED: set[Path] = set()


def get_ui_state_db_path() -> Path:
    data_dir = Path(user_data_dir("Victus", "Victus"))
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "ui_state.sqlite3"


def _connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or get_ui_state_db_path()
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def init_ui_state_db(db_path: Path | None = None) -> Path:
    path = db_path or get_ui_state_db_path()
    if path in _DB_INITIALIZED:
        return path

    with _connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS entities (
                id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                title TEXT NOT NULL,
                detail TEXT NOT NULL,
                status TEXT NOT NULL,
                urgency INTEGER NOT NULL,
                severity TEXT,
                progress INTEGER,
                step INTEGER,
                total_steps INTEGER,
                updated_at INTEGER NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS focus_lane_cards (
                id TEXT PRIMARY KEY,
                kind TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS dialogue_messages (
                id TEXT PRIMARY KEY,
                role TEXT NOT NULL,
                text TEXT NOT NULL,
                created_at INTEGER NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS timeline_events (
                id TEXT PRIMARY KEY,
                label TEXT NOT NULL,
                detail TEXT NOT NULL,
                created_at INTEGER NOT NULL
            )
            """
        )

        row = conn.execute("SELECT COUNT(*) AS count FROM entities").fetchone()
        if row and int(row["count"]) == 0:
            _seed_default_state(conn)

        conn.commit()

    _DB_INITIALIZED.add(path)
    return path


def _seed_default_state(conn: sqlite3.Connection) -> None:
    now = int(time.time() * 1000)
    entities = [
        ("failure-1", "failure", "Orchestrator retry exhausted", "Last retry exceeded policy backoff window.", "open", 90, "critical", None, None, None, now - 2 * 60_000),
        ("approval-1", "approval", "Filesystem tool scope adjustment", "Grant wider read/write scope for migration script.", "pending", 74, None, None, None, None, now - 5 * 60_000),
        ("alert-1", "alert", "Memory latency drift", "95th percentile latency is up 12%.", "open", 67, "warning", None, None, None, now - 15 * 60_000),
        ("reminder-1", "reminder", "Approve onboarding policy edits", "Due today 2:00 PM", "pending", 82, None, None, None, None, now - 12 * 60_000),
        ("workflow-1", "workflow", "Weekly planning synthesis", "Step 3/5 · 60%", "paused", 63, None, 60, 3, 5, now - 40 * 60_000),
    ]
    conn.executemany(
        """
        INSERT INTO entities (id, kind, title, detail, status, urgency, severity, progress, step, total_steps, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        entities,
    )

    for kind in ("failure", "approval", "alert", "reminder", "workflow"):
        conn.execute("INSERT INTO focus_lane_cards (id, kind) VALUES (?, ?)", (f"{kind}-card", kind))

    conn.execute(
        "INSERT INTO dialogue_messages (id, role, text, created_at) VALUES (?, ?, ?, ?)",
        (f"dialogue-{uuid.uuid4().hex}", "system", "Victus is active. Issue a command when ready.", now - 60_000),
    )

    timeline = [
        (f"timeline-{uuid.uuid4().hex}", "Executor heartbeat stable", "Automation channels nominal.", now - 30 * 60_000),
        (f"timeline-{uuid.uuid4().hex}", "Team planning sync", "Agenda locked for tomorrow.", now - 20 * 60_000),
        (f"timeline-{uuid.uuid4().hex}", "Inbox triage complete", "12 items processed.", now - 45 * 60_000),
    ]
    conn.executemany(
        "INSERT INTO timeline_events (id, label, detail, created_at) VALUES (?, ?, ?, ?)",
        timeline,
    )


def fetch_ui_state(db_path: Path | None = None) -> UIState:
    path = init_ui_state_db(db_path)
    with _connect(path) as conn:
        entities = conn.execute("SELECT * FROM entities ORDER BY updated_at DESC").fetchall()
        cards = conn.execute("SELECT id, kind FROM focus_lane_cards").fetchall()
        dialogue = conn.execute("SELECT * FROM dialogue_messages ORDER BY created_at ASC").fetchall()
        timeline = conn.execute("SELECT * FROM timeline_events ORDER BY created_at DESC").fetchall()

    def rows_for(kind: str) -> list[dict[str, object]]:
        return [dict(row) for row in entities if row["kind"] == kind]

    return UIState(
        reminders=rows_for("reminder"),
        approvals=rows_for("approval"),
        alerts=rows_for("alert"),
        failures=rows_for("failure"),
        workflows=rows_for("workflow"),
        focus_lane_cards=[{"id": row["id"], "kind": row["kind"]} for row in cards],
        dialogue_messages=[dict(row) for row in dialogue],
        timeline_events=[dict(row) for row in timeline],
    )


def connection_for_writes(db_path: Path | None = None) -> sqlite3.Connection:
    path = init_ui_state_db(db_path)
    return _connect(path)
