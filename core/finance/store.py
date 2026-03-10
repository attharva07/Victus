from __future__ import annotations

import json
from typing import Any

from core.storage.db import get_connection


def _row_to_transaction(row: Any) -> dict[str, Any]:
    return {
        "id": row["id"],
        "ts": row["ts"],
        "amount_cents": row["amount_cents"],
        "currency": row["currency"],
        "category": row["category"],
        "merchant": row["merchant"],
        "note": row["note"],
        "method": row["method"],
        "source": row["source"],
    }


def add_transaction(record: dict[str, Any]) -> str:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO transactions (
                id, ts, amount_cents, currency, category, merchant, note, method, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["id"],
                record["ts"],
                record["amount_cents"],
                record["currency"],
                record["category"],
                record["merchant"],
                record["note"],
                record["method"],
                record["source"],
            ),
        )
    return record["id"]


def list_transactions(
    start_ts: str | None,
    end_ts: str | None,
    category: str | None,
    limit: int,
) -> list[dict[str, Any]]:
    sql = "SELECT * FROM transactions WHERE 1=1"
    params: list[Any] = []
    if start_ts:
        sql += " AND ts >= ?"
        params.append(start_ts)
    if end_ts:
        sql += " AND ts <= ?"
        params.append(end_ts)
    if category:
        sql += " AND category = ?"
        params.append(category)
    sql += " ORDER BY ts DESC LIMIT ?"
    params.append(limit)
    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_row_to_transaction(row) for row in rows]


def summarize_transactions(
    start_ts: str | None,
    end_ts: str | None,
    group_by: str,
) -> dict[str, int]:
    if group_by not in {"category"}:
        group_by = "category"
    sql = f"SELECT {group_by} as key, SUM(amount_cents) as total FROM transactions WHERE 1=1"
    params: list[Any] = []
    if start_ts:
        sql += " AND ts >= ?"
        params.append(start_ts)
    if end_ts:
        sql += " AND ts <= ?"
        params.append(end_ts)
    sql += f" GROUP BY {group_by}"
    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return {row["key"]: row["total"] for row in rows if row["key"] is not None}


def upsert_rule(rule_key: str, threshold_value: float, enabled: bool, updated_at: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO finance_rules (id, rule_key, threshold_value, enabled, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(rule_key) DO UPDATE SET
                threshold_value = excluded.threshold_value,
                enabled = excluded.enabled,
                updated_at = excluded.updated_at
            """,
            (rule_key, rule_key, threshold_value, 1 if enabled else 0, updated_at),
        )


def list_rules() -> dict[str, dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute("SELECT rule_key, threshold_value, enabled FROM finance_rules").fetchall()
    return {
        row["rule_key"]: {"threshold_value": float(row["threshold_value"]), "enabled": bool(row["enabled"])}
        for row in rows
    }


def add_alert(record: dict[str, Any]) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO finance_alerts (
                id, severity, title, message, reason, entity_type, entity_id, suggested_next_step, ts, acked
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["id"],
                record["severity"],
                record["title"],
                record["message"],
                record["reason"],
                record.get("entity_type"),
                record.get("entity_id"),
                record.get("suggested_next_step"),
                record["ts"],
                1 if record.get("acked", False) else 0,
            ),
        )


def list_alerts(limit: int = 100) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM finance_alerts ORDER BY ts DESC LIMIT ?", (limit,)).fetchall()
    return [dict(row) for row in rows]


def add_behavior_log(record: dict[str, Any]) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO finance_behavior_logs (id, behavior_type, score, details, ts)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                record["id"],
                record["behavior_type"],
                record["score"],
                json.dumps(record.get("details", {}), sort_keys=True),
                record["ts"],
            ),
        )


def list_behavior_logs(limit: int = 200) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM finance_behavior_logs ORDER BY ts DESC LIMIT ?", (limit,)).fetchall()
    parsed: list[dict[str, Any]] = []
    for row in rows:
        record = dict(row)
        try:
            record["details"] = json.loads(record.get("details") or "{}")
        except json.JSONDecodeError:
            record["details"] = {}
        parsed.append(record)
    return parsed
