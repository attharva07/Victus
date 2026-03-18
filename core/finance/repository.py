from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from core.storage.db import get_connection, init_db

from .entities import Account, Alert, Bill, Budget, Category, SavingsGoal, Transaction
from .policy import FinanceConflictError


def utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


class FinanceRepository:
    def __init__(self) -> None:
        init_db()

    # -----------------------------------------------------------------------
    # Accounts
    # -----------------------------------------------------------------------

    def create_account(self, *, account_id: str | None, name: str, account_type: str, currency: str, institution: str | None, is_active: bool) -> Account:
        resolved_id = account_id or str(uuid4())
        now = utc_now_iso()
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO finance_accounts (id, name, account_type, currency, institution, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    account_type = excluded.account_type,
                    currency = excluded.currency,
                    institution = excluded.institution,
                    is_active = excluded.is_active,
                    updated_at = excluded.updated_at
                """,
                (resolved_id, name, account_type, currency, institution, 1 if is_active else 0, now, now),
            )
            row = conn.execute("SELECT * FROM finance_accounts WHERE id = ?", (resolved_id,)).fetchone()
        if row is None:
            raise FinanceConflictError(f"Unable to persist account '{resolved_id}'")
        return self._row_to_account(row)

    def get_account(self, account_id: str) -> Account | None:
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM finance_accounts WHERE id = ?", (account_id,)).fetchone()
        return self._row_to_account(row) if row else None

    def update_account(self, account_id: str, updates: dict[str, Any]) -> Account | None:
        if not updates:
            return self.get_account(account_id)
        updates["updated_at"] = utc_now_iso()
        assignments = ", ".join(f"{key} = ?" for key in updates)
        params = list(updates.values()) + [account_id]
        with get_connection() as conn:
            conn.execute(f"UPDATE finance_accounts SET {assignments} WHERE id = ?", params)
            row = conn.execute("SELECT * FROM finance_accounts WHERE id = ?", (account_id,)).fetchone()
        return self._row_to_account(row) if row else None

    def list_accounts(self, *, active_only: bool = True) -> list[Account]:
        sql = "SELECT * FROM finance_accounts"
        params: list[Any] = []
        if active_only:
            sql += " WHERE is_active = 1"
        sql += " ORDER BY name ASC"
        with get_connection() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._row_to_account(row) for row in rows]

    # -----------------------------------------------------------------------
    # Categories
    # -----------------------------------------------------------------------

    def create_category(self, *, category_id: str | None, name: str, cat_type: str, parent_category: str | None, is_system: bool) -> Category:
        resolved_id = category_id or str(uuid4())
        now = utc_now_iso()
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO finance_categories (id, name, type, parent_category, is_system, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 1, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    type = excluded.type,
                    parent_category = excluded.parent_category,
                    updated_at = excluded.updated_at
                """,
                (resolved_id, name, cat_type, parent_category, 1 if is_system else 0, now, now),
            )
            row = conn.execute("SELECT * FROM finance_categories WHERE id = ?", (resolved_id,)).fetchone()
        assert row is not None
        return self._row_to_category(row)

    def get_category(self, category_id: str) -> Category | None:
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM finance_categories WHERE id = ?", (category_id,)).fetchone()
        return self._row_to_category(row) if row else None

    def get_category_by_name(self, name: str) -> Category | None:
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM finance_categories WHERE name = ?", (name,)).fetchone()
        return self._row_to_category(row) if row else None

    def update_category(self, category_id: str, updates: dict[str, Any]) -> Category | None:
        if not updates:
            return self.get_category(category_id)
        updates["updated_at"] = utc_now_iso()
        assignments = ", ".join(f"{key} = ?" for key in updates)
        params = list(updates.values()) + [category_id]
        with get_connection() as conn:
            conn.execute(f"UPDATE finance_categories SET {assignments} WHERE id = ?", params)
            row = conn.execute("SELECT * FROM finance_categories WHERE id = ?", (category_id,)).fetchone()
        return self._row_to_category(row) if row else None

    def list_categories(self, *, active_only: bool = True) -> list[Category]:
        sql = "SELECT * FROM finance_categories"
        if active_only:
            sql += " WHERE is_active = 1"
        sql += " ORDER BY name ASC"
        with get_connection() as conn:
            rows = conn.execute(sql).fetchall()
        return [self._row_to_category(row) for row in rows]

    def ensure_category(self, name: str, cat_type: str = "expense") -> Category:
        existing = self.get_category_by_name(name)
        if existing:
            return existing
        return self.create_category(category_id=None, name=name, cat_type=cat_type, parent_category=None, is_system=False)

    # -----------------------------------------------------------------------
    # Transactions
    # -----------------------------------------------------------------------

    def create_transaction(self, record: dict[str, Any]) -> Transaction:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO transactions (
                    id, ts, amount_cents, currency, merchant, transaction_date,
                    category_id, account_id, direction, payment_method, notes,
                    source, tags, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["id"],
                    record.get("ts", record["created_at"]),
                    record["amount_cents"],
                    record["currency"],
                    record.get("merchant"),
                    record["transaction_date"],
                    record["category_id"],
                    record.get("account_id"),
                    record["direction"],
                    record.get("payment_method"),
                    record.get("notes"),
                    record.get("source"),
                    record.get("tags"),
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
        updates["updated_at"] = utc_now_iso()
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
        date_from: str | None = None,
        date_to: str | None = None,
        category: str | None = None,
        account_id: str | None = None,
        direction: str | None = None,
        merchant: str | None = None,
        limit: int = 50,
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
            sql += " AND (category_id = ? OR category_id IN (SELECT id FROM finance_categories WHERE LOWER(name) = LOWER(?)))"
            params.extend([category, category])
        if account_id:
            sql += " AND account_id = ?"
            params.append(account_id)
        if direction:
            sql += " AND direction = ?"
            params.append(direction)
        if merchant:
            sql += " AND merchant = ?"
            params.append(merchant)
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
        expense_cents = sum(abs(tx.amount_cents) for tx in transactions if tx.direction == "expense")
        income_cents = sum(abs(tx.amount_cents) for tx in transactions if tx.direction == "income")
        by_category: dict[str, int] = {}
        by_account: dict[str, int] = {}
        by_merchant: dict[str, int] = {}
        by_direction: dict[str, int] = {}
        for tx in transactions:
            abs_amount = abs(tx.amount_cents)
            cat_key = tx.category_id or "uncategorized"
            by_category[cat_key] = by_category.get(cat_key, 0) + abs_amount
            account_key = tx.account_id or "unassigned"
            by_account[account_key] = by_account.get(account_key, 0) + abs_amount
            merchant_key = tx.merchant or "unknown"
            by_merchant[merchant_key] = by_merchant.get(merchant_key, 0) + abs_amount
            by_direction[tx.direction] = by_direction.get(tx.direction, 0) + abs_amount
        return {
            "transactions": transactions,
            "income_cents": income_cents,
            "expense_cents": expense_cents,
            "net_cents": income_cents - expense_cents,
            "by_category": dict(sorted(by_category.items())),
            "by_account": dict(sorted(by_account.items())),
            "by_merchant": dict(sorted(by_merchant.items(), key=lambda x: -x[1])),
            "by_direction": by_direction,
        }

    # -----------------------------------------------------------------------
    # Budgets
    # -----------------------------------------------------------------------

    def create_budget(self, record: dict[str, Any]) -> Budget:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO finance_budgets (
                    id, name, category_id, account_id, amount_limit_cents,
                    currency, period, warning_threshold_percent, is_active,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (
                    record["id"], record["name"], record.get("category_id"),
                    record.get("account_id"), record["amount_limit_cents"],
                    record["currency"], record["period"],
                    record["warning_threshold_percent"],
                    record["created_at"], record["updated_at"],
                ),
            )
            row = conn.execute("SELECT * FROM finance_budgets WHERE id = ?", (record["id"],)).fetchone()
        assert row is not None
        return self._row_to_budget(row)

    def get_budget(self, budget_id: str) -> Budget | None:
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM finance_budgets WHERE id = ?", (budget_id,)).fetchone()
        return self._row_to_budget(row) if row else None

    def update_budget(self, budget_id: str, updates: dict[str, Any]) -> Budget | None:
        if not updates:
            return self.get_budget(budget_id)
        updates["updated_at"] = utc_now_iso()
        assignments = ", ".join(f"{key} = ?" for key in updates)
        params = list(updates.values()) + [budget_id]
        with get_connection() as conn:
            conn.execute(f"UPDATE finance_budgets SET {assignments} WHERE id = ?", params)
            row = conn.execute("SELECT * FROM finance_budgets WHERE id = ?", (budget_id,)).fetchone()
        return self._row_to_budget(row) if row else None

    def delete_budget(self, budget_id: str) -> bool:
        with get_connection() as conn:
            cursor = conn.execute("DELETE FROM finance_budgets WHERE id = ?", (budget_id,))
        return cursor.rowcount > 0

    def list_budgets(self, *, active_only: bool = True) -> list[Budget]:
        sql = "SELECT * FROM finance_budgets"
        if active_only:
            sql += " WHERE is_active = 1"
        sql += " ORDER BY name ASC"
        with get_connection() as conn:
            rows = conn.execute(sql).fetchall()
        return [self._row_to_budget(row) for row in rows]

    # -----------------------------------------------------------------------
    # Bills / Obligations
    # -----------------------------------------------------------------------

    def create_bill(self, record: dict[str, Any]) -> Bill:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO finance_bills (
                    id, name, amount_expected_cents, currency, due_date,
                    recurrence_rule, category_id, account_id, status,
                    auto_reminder, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?)
                """,
                (
                    record["id"], record["name"], record.get("amount_expected_cents"),
                    record["currency"], record["due_date"],
                    record.get("recurrence_rule"), record.get("category_id"),
                    record.get("account_id"),
                    1 if record.get("auto_reminder", True) else 0,
                    record.get("notes"),
                    record["created_at"], record["updated_at"],
                ),
            )
            row = conn.execute("SELECT * FROM finance_bills WHERE id = ?", (record["id"],)).fetchone()
        assert row is not None
        return self._row_to_bill(row)

    def get_bill(self, bill_id: str) -> Bill | None:
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM finance_bills WHERE id = ?", (bill_id,)).fetchone()
        return self._row_to_bill(row) if row else None

    def update_bill(self, bill_id: str, updates: dict[str, Any]) -> Bill | None:
        if not updates:
            return self.get_bill(bill_id)
        updates["updated_at"] = utc_now_iso()
        assignments = ", ".join(f"{key} = ?" for key in updates)
        params = list(updates.values()) + [bill_id]
        with get_connection() as conn:
            conn.execute(f"UPDATE finance_bills SET {assignments} WHERE id = ?", params)
            row = conn.execute("SELECT * FROM finance_bills WHERE id = ?", (bill_id,)).fetchone()
        return self._row_to_bill(row) if row else None

    def delete_bill(self, bill_id: str) -> bool:
        with get_connection() as conn:
            cursor = conn.execute("DELETE FROM finance_bills WHERE id = ?", (bill_id,))
        return cursor.rowcount > 0

    def list_bills(self, *, status_filter: str | None = None) -> list[Bill]:
        sql = "SELECT * FROM finance_bills"
        params: list[Any] = []
        if status_filter:
            sql += " WHERE status = ?"
            params.append(status_filter)
        sql += " ORDER BY due_date ASC"
        with get_connection() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._row_to_bill(row) for row in rows]

    def get_due_bills(self, *, before_date: str) -> list[Bill]:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM finance_bills WHERE due_date <= ? AND status IN ('pending', 'overdue') ORDER BY due_date ASC",
                (before_date,),
            ).fetchall()
        return [self._row_to_bill(row) for row in rows]

    # -----------------------------------------------------------------------
    # Savings Goals
    # -----------------------------------------------------------------------

    def create_savings_goal(self, record: dict[str, Any]) -> SavingsGoal:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO finance_savings_goals (
                    id, name, target_amount_cents, currency, target_date,
                    linked_account_id, current_progress_cents, status,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, 0, 'active', ?, ?)
                """,
                (
                    record["id"], record["name"], record["target_amount_cents"],
                    record["currency"], record.get("target_date"),
                    record.get("linked_account_id"),
                    record["created_at"], record["updated_at"],
                ),
            )
            row = conn.execute("SELECT * FROM finance_savings_goals WHERE id = ?", (record["id"],)).fetchone()
        assert row is not None
        return self._row_to_savings_goal(row)

    def get_savings_goal(self, goal_id: str) -> SavingsGoal | None:
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM finance_savings_goals WHERE id = ?", (goal_id,)).fetchone()
        return self._row_to_savings_goal(row) if row else None

    def update_savings_goal(self, goal_id: str, updates: dict[str, Any]) -> SavingsGoal | None:
        if not updates:
            return self.get_savings_goal(goal_id)
        updates["updated_at"] = utc_now_iso()
        assignments = ", ".join(f"{key} = ?" for key in updates)
        params = list(updates.values()) + [goal_id]
        with get_connection() as conn:
            conn.execute(f"UPDATE finance_savings_goals SET {assignments} WHERE id = ?", params)
            row = conn.execute("SELECT * FROM finance_savings_goals WHERE id = ?", (goal_id,)).fetchone()
        return self._row_to_savings_goal(row) if row else None

    def record_savings_progress(self, goal_id: str, amount_cents: int) -> SavingsGoal | None:
        now = utc_now_iso()
        with get_connection() as conn:
            conn.execute(
                "UPDATE finance_savings_goals SET current_progress_cents = current_progress_cents + ?, updated_at = ? WHERE id = ?",
                (amount_cents, now, goal_id),
            )
            conn.execute(
                "INSERT INTO finance_savings_contributions (id, goal_id, amount_cents, ts, source) VALUES (?, ?, ?, ?, ?)",
                (str(uuid4()), goal_id, amount_cents, now, "manual"),
            )
            row = conn.execute("SELECT * FROM finance_savings_goals WHERE id = ?", (goal_id,)).fetchone()
        return self._row_to_savings_goal(row) if row else None

    def list_savings_goals(self, *, active_only: bool = True) -> list[SavingsGoal]:
        sql = "SELECT * FROM finance_savings_goals"
        if active_only:
            sql += " WHERE status = 'active'"
        sql += " ORDER BY name ASC"
        with get_connection() as conn:
            rows = conn.execute(sql).fetchall()
        return [self._row_to_savings_goal(row) for row in rows]

    # -----------------------------------------------------------------------
    # Alerts
    # -----------------------------------------------------------------------

    def create_alert(self, record: dict[str, Any]) -> Alert:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO finance_alerts (
                    id, type, severity, title, message, source_rule,
                    related_entity_type, related_entity_id, created_at,
                    resolved_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, 'active')
                """,
                (
                    record["id"], record["type"], record["severity"],
                    record["title"], record["message"], record["source_rule"],
                    record.get("related_entity_type"), record.get("related_entity_id"),
                    record["created_at"],
                ),
            )
            row = conn.execute("SELECT * FROM finance_alerts WHERE id = ?", (record["id"],)).fetchone()
        assert row is not None
        return self._row_to_alert(row)

    def resolve_alert(self, alert_id: str) -> Alert | None:
        now = utc_now_iso()
        with get_connection() as conn:
            conn.execute(
                "UPDATE finance_alerts SET status = 'resolved', resolved_at = ? WHERE id = ?",
                (now, alert_id),
            )
            row = conn.execute("SELECT * FROM finance_alerts WHERE id = ?", (alert_id,)).fetchone()
        return self._row_to_alert(row) if row else None

    def list_alerts(self, *, limit: int = 100, active_only: bool = False) -> list[Alert]:
        sql = "SELECT * FROM finance_alerts"
        if active_only:
            sql += " WHERE status = 'active'"
        sql += " ORDER BY created_at DESC LIMIT ?"
        with get_connection() as conn:
            rows = conn.execute(sql, (limit,)).fetchall()
        return [self._row_to_alert(row) for row in rows]

    # -----------------------------------------------------------------------
    # Rules (legacy support)
    # -----------------------------------------------------------------------

    def upsert_rule(self, rule_key: str, threshold_value: float, enabled: bool) -> None:
        now = utc_now_iso()
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
                (rule_key, rule_key, threshold_value, 1 if enabled else 0, now),
            )

    def list_rules(self) -> dict[str, dict[str, Any]]:
        with get_connection() as conn:
            rows = conn.execute("SELECT rule_key, threshold_value, enabled FROM finance_rules").fetchall()
        return {
            row["rule_key"]: {"threshold_value": float(row["threshold_value"]), "enabled": bool(row["enabled"])}
            for row in rows
        }

    # -----------------------------------------------------------------------
    # Behavior logs (legacy support)
    # -----------------------------------------------------------------------

    def add_behavior_log(self, record: dict[str, Any]) -> None:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO finance_behavior_logs (id, behavior_type, score, details, ts) VALUES (?, ?, ?, ?, ?)",
                (record["id"], record["behavior_type"], record["score"], json.dumps(record.get("details", {}), sort_keys=True), record["ts"]),
            )

    def list_behavior_logs(self, limit: int = 200) -> list[dict[str, Any]]:
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

    # -----------------------------------------------------------------------
    # Row mappers
    # -----------------------------------------------------------------------

    @staticmethod
    def _row_to_account(row: Any) -> Account:
        keys = row.keys() if hasattr(row, "keys") else []
        return Account(
            id=row["id"],
            name=row["name"],
            account_type=row["account_type"],
            currency=row["currency"] if "currency" in keys else "USD",
            institution=row["institution"],
            is_active=bool(row["is_active"]),
            created_at=row["created_at"] or "",
            updated_at=row["updated_at"] if "updated_at" in keys else row["created_at"] or "",
        )

    @staticmethod
    def _row_to_category(row: Any) -> Category:
        keys = row.keys() if hasattr(row, "keys") else []
        return Category(
            id=row["id"] if "id" in keys else row.get("key", ""),
            name=row["name"] if "name" in keys else row.get("display_name", ""),
            type=row["type"] if "type" in keys else "expense",
            parent_category=row["parent_category"] if "parent_category" in keys else None,
            is_system=bool(row["is_system"]) if "is_system" in keys else False,
            is_active=bool(row["is_active"]) if "is_active" in keys else True,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _row_to_transaction(row: Any) -> Transaction:
        keys = row.keys() if hasattr(row, "keys") else []
        transaction_date = row["transaction_date"] if "transaction_date" in keys else ""
        if not transaction_date and "ts" in keys:
            transaction_date = str(row["ts"])[:10]
        created_at = row["created_at"] if "created_at" in keys else ""
        if not created_at and "ts" in keys:
            created_at = row["ts"]
        updated_at = row["updated_at"] if "updated_at" in keys else ""
        if not updated_at and "ts" in keys:
            updated_at = row["ts"]
        # Support both old 'category' and new 'category_id' column names
        category_id = ""
        if "category_id" in keys and row["category_id"]:
            category_id = row["category_id"]
        elif "category" in keys and row["category"]:
            category_id = row["category"]
        # Support both old 'note' and new 'notes' column names
        notes = None
        if "notes" in keys:
            notes = row["notes"]
        elif "note" in keys:
            notes = row["note"]
        return Transaction(
            id=row["id"],
            amount_cents=int(row["amount_cents"]),
            currency=row["currency"],
            merchant=row["merchant"],
            transaction_date=transaction_date or "",
            category_id=category_id,
            account_id=row["account_id"] if "account_id" in keys else None,
            direction=row["direction"] if "direction" in keys else ("expense" if int(row["amount_cents"]) < 0 else "income"),
            payment_method=row["payment_method"] if "payment_method" in keys else (row["method"] if "method" in keys else None),
            notes=notes,
            source=row["source"] if "source" in keys else None,
            tags=row["tags"] if "tags" in keys else None,
            created_at=created_at or "",
            updated_at=updated_at or "",
        )

    @staticmethod
    def _row_to_budget(row: Any) -> Budget:
        keys = row.keys() if hasattr(row, "keys") else []
        return Budget(
            id=row["id"],
            name=row["name"] if "name" in keys else "",
            category_id=row["category_id"] if "category_id" in keys else None,
            account_id=row["account_id"] if "account_id" in keys else None,
            amount_limit_cents=int(row["amount_limit_cents"]) if "amount_limit_cents" in keys else int(row.get("total_limit_cents", 0)),
            currency=row["currency"] if "currency" in keys else "USD",
            period=row["period"] if "period" in keys else "monthly",
            warning_threshold_percent=int(row["warning_threshold_percent"]) if "warning_threshold_percent" in keys else 80,
            is_active=bool(row["is_active"]) if "is_active" in keys else True,
            created_at=row["created_at"] if "created_at" in keys else "",
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _row_to_bill(row: Any) -> Bill:
        return Bill(
            id=row["id"],
            name=row["name"],
            amount_expected_cents=int(row["amount_expected_cents"]) if row["amount_expected_cents"] is not None else None,
            currency=row["currency"],
            due_date=row["due_date"],
            recurrence_rule=row["recurrence_rule"],
            category_id=row["category_id"],
            account_id=row["account_id"],
            status=row["status"],
            auto_reminder=bool(row["auto_reminder"]),
            notes=row["notes"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _row_to_savings_goal(row: Any) -> SavingsGoal:
        keys = row.keys() if hasattr(row, "keys") else []
        return SavingsGoal(
            id=row["id"],
            name=row["name"],
            target_amount_cents=int(row["target_amount_cents"]) if "target_amount_cents" in keys else int(row.get("target_cents", 0)),
            currency=row["currency"] if "currency" in keys else "USD",
            target_date=row["target_date"],
            linked_account_id=row["linked_account_id"] if "linked_account_id" in keys else None,
            current_progress_cents=int(row["current_progress_cents"]) if "current_progress_cents" in keys else int(row.get("current_cents", 0)),
            status=row["status"] if "status" in keys else "active",
            created_at=row["created_at"] if "created_at" in keys else "",
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _row_to_alert(row: Any) -> Alert:
        keys = row.keys() if hasattr(row, "keys") else []
        return Alert(
            id=row["id"],
            type=row["type"] if "type" in keys else "",
            severity=row["severity"],
            title=row["title"],
            message=row["message"],
            source_rule=row["source_rule"] if "source_rule" in keys else row.get("reason", ""),
            related_entity_type=row["related_entity_type"] if "related_entity_type" in keys else row.get("entity_type"),
            related_entity_id=row["related_entity_id"] if "related_entity_id" in keys else row.get("entity_id"),
            created_at=row["created_at"] if "created_at" in keys else row.get("ts", ""),
            resolved_at=row["resolved_at"] if "resolved_at" in keys else None,
            status=row["status"] if "status" in keys else "active",
        )
