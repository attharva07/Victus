from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from core.storage.db import get_connection, init_db

from .entities import Account, Category, Transaction
from .policy import FinanceConflictError


def utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


class FinanceRepository:
    def __init__(self) -> None:
        init_db()
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        with get_connection() as conn:
            self._ensure_table(conn, "transactions", {
                "transaction_date": "TEXT",
                "account_id": "TEXT",
                "created_at": "TEXT",
                "updated_at": "TEXT",
            })
            self._ensure_table(conn, "finance_accounts", {
                "institution": "TEXT",
                "is_active": "INTEGER NOT NULL DEFAULT 1",
                "created_at": "TEXT NOT NULL DEFAULT ''",
            })
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS finance_categories (
                    key TEXT PRIMARY KEY,
                    display_name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            now = utc_now_iso()
            conn.execute(
                """
                UPDATE transactions
                SET transaction_date = COALESCE(NULLIF(transaction_date, ''), substr(ts, 1, 10)),
                    created_at = COALESCE(NULLIF(created_at, ''), ts),
                    updated_at = COALESCE(NULLIF(updated_at, ''), ts)
                WHERE transaction_date IS NULL OR transaction_date = ''
                   OR created_at IS NULL OR created_at = ''
                   OR updated_at IS NULL OR updated_at = ''
                """
            )
            conn.execute("UPDATE finance_accounts SET created_at = ? WHERE created_at IS NULL OR created_at = ''", (now,))

    @staticmethod
    def _ensure_table(conn: Any, table_name: str, columns: Mapping[str, str]) -> None:
        existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()}
        for column_name, column_sql in columns.items():
            if column_name not in existing:
                conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}")

    def upsert_account(self, *, account_id: str | None, name: str, account_type: str, institution: str | None, is_active: bool) -> Account:
        resolved_id = account_id or str(uuid4())
        created_at = utc_now_iso()
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO finance_accounts (id, name, account_type, institution, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    account_type = excluded.account_type,
                    institution = excluded.institution,
                    is_active = excluded.is_active
                """,
                (resolved_id, name, account_type, institution, 1 if is_active else 0, created_at),
            )
            row = conn.execute("SELECT * FROM finance_accounts WHERE id = ?", (resolved_id,)).fetchone()
        if row is None:
            raise FinanceConflictError(f"Unable to persist account '{resolved_id}'")
        return self._row_to_account(row)

    def get_account(self, account_id: str) -> Account | None:
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM finance_accounts WHERE id = ?", (account_id,)).fetchone()
        return self._row_to_account(row) if row else None

    def create_or_get_category(self, key: str) -> Category:
        display_name = key.replace("_", " ").title()
        now = utc_now_iso()
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO finance_categories (key, display_name, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    display_name = excluded.display_name,
                    updated_at = excluded.updated_at
                """,
                (key, display_name, now, now),
            )
            row = conn.execute("SELECT * FROM finance_categories WHERE key = ?", (key,)).fetchone()
        assert row is not None
        return self._row_to_category(row)

    def create_transaction(self, record: dict[str, Any]) -> Transaction:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO transactions (
                    id, ts, transaction_date, amount_cents, currency, category,
                    merchant, note, account_id, method, source, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["id"],
                    record["ts"],
                    record["transaction_date"],
                    record["amount_cents"],
                    record["currency"],
                    record["category"],
                    record.get("merchant"),
                    record.get("note"),
                    record.get("account_id"),
                    record.get("method"),
                    record["source"],
                    record["created_at"],
                    record["updated_at"],
                ),
            )
            row = conn.execute("SELECT * FROM transactions WHERE id = ?", (record["id"],)).fetchone()
        assert row is not None
        return self._row_to_transaction(row)

    def get_transaction(self, transaction_id: str) -> Transaction | None:
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,)).fetchone()
        return self._row_to_transaction(row) if row else None

    def update_transaction(self, transaction_id: str, updates: dict[str, Any]) -> Transaction | None:
        if not updates:
            return self.get_transaction(transaction_id)
        assignments = ", ".join(f"{key} = ?" for key in updates)
        params = list(updates.values()) + [transaction_id]
        with get_connection() as conn:
            conn.execute(f"UPDATE transactions SET {assignments} WHERE id = ?", params)
            row = conn.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,)).fetchone()
        return self._row_to_transaction(row) if row else None

    def delete_transaction(self, transaction_id: str) -> bool:
        with get_connection() as conn:
            cursor = conn.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        return cursor.rowcount > 0

    def list_transactions(
        self,
        *,
        date_from: str | None,
        date_to: str | None,
        category: str | None,
        account_id: str | None,
        limit: int,
    ) -> list[Transaction]:
        sql = "SELECT * FROM transactions WHERE 1=1"
        params: list[Any] = []
        if date_from:
            sql += " AND transaction_date >= ?"
            params.append(date_from)
        if date_to:
            sql += " AND transaction_date <= ?"
            params.append(date_to)
        if category:
            sql += " AND category = ?"
            params.append(category)
        if account_id:
            sql += " AND account_id = ?"
            params.append(account_id)
        sql += " ORDER BY transaction_date DESC, updated_at DESC, id DESC LIMIT ?"
        params.append(limit)
        with get_connection() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._row_to_transaction(row) for row in rows]

    def summarize_spending(self, *, date_from: str, date_to: str, account_id: str | None) -> dict[str, Any]:
        sql = "SELECT * FROM transactions WHERE transaction_date >= ? AND transaction_date <= ?"
        params: list[Any] = [date_from, date_to]
        if account_id:
            sql += " AND account_id = ?"
            params.append(account_id)
        with get_connection() as conn:
            rows = conn.execute(sql, params).fetchall()
        transactions = [self._row_to_transaction(row) for row in rows]
        expense_cents = sum(abs(tx.amount_cents) for tx in transactions if tx.amount_cents < 0)
        income_cents = sum(tx.amount_cents for tx in transactions if tx.amount_cents > 0)
        by_category: dict[str, int] = {}
        by_account: dict[str, int] = {}
        for tx in transactions:
            if tx.amount_cents < 0:
                by_category[tx.category] = by_category.get(tx.category, 0) + abs(tx.amount_cents)
                account_key = tx.account_id or "unassigned"
                by_account[account_key] = by_account.get(account_key, 0) + abs(tx.amount_cents)
        return {
            "transactions": transactions,
            "income_cents": income_cents,
            "expense_cents": expense_cents,
            "net_cents": income_cents - expense_cents,
            "by_category": dict(sorted(by_category.items())),
            "by_account": dict(sorted(by_account.items())),
        }

    @staticmethod
    def _row_to_transaction(row: Any) -> Transaction:
        transaction_date = row["transaction_date"] or str(row["ts"])[:10]
        created_at = row["created_at"] or row["ts"]
        updated_at = row["updated_at"] or row["ts"]
        return Transaction(
            id=row["id"],
            transaction_date=transaction_date,
            amount_cents=int(row["amount_cents"]),
            currency=row["currency"],
            category=row["category"],
            merchant=row["merchant"],
            note=row["note"],
            account_id=row["account_id"] if "account_id" in row.keys() else None,
            method=row["method"],
            source=row["source"],
            created_at=created_at,
            updated_at=updated_at,
        )

    @staticmethod
    def _row_to_account(row: Any) -> Account:
        return Account(
            id=row["id"],
            name=row["name"],
            account_type=row["account_type"],
            institution=row["institution"],
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
        )

    @staticmethod
    def _row_to_category(row: Any) -> Category:
        return Category(
            key=row["key"],
            display_name=row["display_name"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
