from pathlib import Path

from fastapi.testclient import TestClient

from apps.local.main import create_app
from victus.ui_state import store


def test_approve_and_deny_updates_ui_state(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "ui_state.sqlite3"
    monkeypatch.setattr(store, "get_ui_state_db_path", lambda: db_path)
    store._DB_INITIALIZED.clear()

    app = create_app()
    client = TestClient(app)

    state = client.get("/api/ui/state")
    assert state.status_code == 200
    payload = state.json()
    assert any(item["id"] == "approval-1" for item in payload["approvals"])

    approved = client.post("/api/approvals/approval-1/approve")
    assert approved.status_code == 200
    approved_payload = approved.json()
    assert approved_payload["approvals"] == []
    assert any("(approved)" in event["label"] for event in approved_payload["timeline_events"])

    with store.connection_for_writes(db_path) as conn:
        conn.execute(
            """
            INSERT INTO entities (id, kind, title, detail, status, urgency, severity, progress, step, total_steps, updated_at)
            VALUES (?, 'approval', ?, ?, 'pending', 50, NULL, NULL, NULL, NULL, ?)
            """,
            ("approval-2", "Manual escalation", "Escalation requested", 1000),
        )
        conn.commit()

    denied = client.post("/api/approvals/approval-2/deny")
    assert denied.status_code == 200
    denied_payload = denied.json()
    assert all(item["id"] != "approval-2" for item in denied_payload["approvals"])
    assert any("(denied)" in event["label"] for event in denied_payload["timeline_events"])
