from __future__ import annotations

import sqlite3
from pathlib import Path

from core.config import ensure_directories

_DB_INITIALIZED: set[Path] = set()


def get_db_path() -> Path:
    paths = ensure_directories()
    return paths.data_dir / "victus_local.sqlite3"


def init_db() -> None:
    db_path = get_db_path()
    if db_path in _DB_INITIALIZED:
        return
    conn = sqlite3.connect(str(db_path))
    try:
        # -- Memory domain ---------------------------------------------------
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                ts TEXT,
                type TEXT,
                tags TEXT,
                source TEXT,
                content TEXT,
                importance INTEGER,
                confidence REAL
            )
            """
        )
        columns = {row[1] for row in conn.execute("PRAGMA table_info(memories)").fetchall()}
        if "sensitivity" not in columns:
            conn.execute("ALTER TABLE memories ADD COLUMN sensitivity TEXT DEFAULT 'internal'")

        # -- Finance domain: Accounts ----------------------------------------
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS finance_accounts (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                account_type TEXT NOT NULL,
                currency TEXT NOT NULL DEFAULT 'USD',
                institution TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        _ensure_columns(conn, "finance_accounts", {
            "currency": "TEXT NOT NULL DEFAULT 'USD'",
            "updated_at": "TEXT NOT NULL DEFAULT ''",
        })

        # -- Finance domain: Categories --------------------------------------
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS finance_categories (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL DEFAULT 'expense',
                parent_category TEXT,
                is_system INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        _ensure_columns(conn, "finance_categories", {
            "id": None,  # PK exists
            "type": "TEXT NOT NULL DEFAULT 'expense'",
            "parent_category": "TEXT",
            "is_system": "INTEGER NOT NULL DEFAULT 0",
            "is_active": "INTEGER NOT NULL DEFAULT 1",
        })

        # -- Finance domain: Transactions ------------------------------------
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY,
                ts TEXT,
                amount_cents INTEGER NOT NULL,
                currency TEXT NOT NULL DEFAULT 'USD',
                merchant TEXT,
                transaction_date TEXT,
                category_id TEXT,
                account_id TEXT,
                direction TEXT NOT NULL DEFAULT 'expense',
                payment_method TEXT,
                notes TEXT,
                source TEXT,
                tags TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )
        _ensure_columns(conn, "transactions", {
            "transaction_date": "TEXT",
            "account_id": "TEXT",
            "direction": "TEXT NOT NULL DEFAULT 'expense'",
            "payment_method": "TEXT",
            "notes": "TEXT",
            "tags": "TEXT",
            "category_id": "TEXT",
            "created_at": "TEXT",
            "updated_at": "TEXT",
        })

        # -- Finance domain: Budgets -----------------------------------------
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS finance_budgets (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category_id TEXT,
                account_id TEXT,
                amount_limit_cents INTEGER NOT NULL,
                currency TEXT NOT NULL DEFAULT 'USD',
                period TEXT NOT NULL DEFAULT 'monthly',
                warning_threshold_percent INTEGER NOT NULL DEFAULT 80,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        _ensure_columns(conn, "finance_budgets", {
            "name": "TEXT NOT NULL DEFAULT ''",
            "category_id": "TEXT",
            "account_id": "TEXT",
            "amount_limit_cents": "INTEGER NOT NULL DEFAULT 0",
            "currency": "TEXT NOT NULL DEFAULT 'USD'",
            "period": "TEXT NOT NULL DEFAULT 'monthly'",
            "warning_threshold_percent": "INTEGER NOT NULL DEFAULT 80",
            "is_active": "INTEGER NOT NULL DEFAULT 1",
            "created_at": "TEXT NOT NULL DEFAULT ''",
        })

        # -- Finance domain: Bills / Obligations -----------------------------
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS finance_bills (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                amount_expected_cents INTEGER,
                currency TEXT NOT NULL DEFAULT 'USD',
                due_date TEXT NOT NULL,
                recurrence_rule TEXT,
                category_id TEXT,
                account_id TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                auto_reminder INTEGER NOT NULL DEFAULT 1,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        # -- Finance domain: Savings Goals -----------------------------------
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS finance_savings_goals (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                target_amount_cents INTEGER NOT NULL,
                currency TEXT NOT NULL DEFAULT 'USD',
                target_date TEXT,
                linked_account_id TEXT,
                current_progress_cents INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        _ensure_columns(conn, "finance_savings_goals", {
            "target_amount_cents": "INTEGER NOT NULL DEFAULT 0",
            "currency": "TEXT NOT NULL DEFAULT 'USD'",
            "linked_account_id": "TEXT",
            "current_progress_cents": "INTEGER NOT NULL DEFAULT 0",
            "status": "TEXT NOT NULL DEFAULT 'active'",
            "created_at": "TEXT NOT NULL DEFAULT ''",
        })

        # -- Finance domain: Alerts ------------------------------------------
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS finance_alerts (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                severity TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                source_rule TEXT NOT NULL,
                related_entity_type TEXT,
                related_entity_id TEXT,
                created_at TEXT NOT NULL,
                resolved_at TEXT,
                status TEXT NOT NULL DEFAULT 'active'
            )
            """
        )
        _ensure_columns(conn, "finance_alerts", {
            "type": "TEXT NOT NULL DEFAULT ''",
            "source_rule": "TEXT NOT NULL DEFAULT ''",
            "related_entity_type": "TEXT",
            "related_entity_id": "TEXT",
            "resolved_at": "TEXT",
            "status": "TEXT NOT NULL DEFAULT 'active'",
        })

        # -- Finance domain: Behavior Logs -----------------------------------
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS finance_behavior_logs (
                id TEXT PRIMARY KEY,
                behavior_type TEXT NOT NULL,
                score REAL NOT NULL,
                details TEXT,
                ts TEXT NOT NULL
            )
            """
        )

        # -- Finance domain: Rules -------------------------------------------
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS finance_rules (
                id TEXT PRIMARY KEY,
                rule_key TEXT NOT NULL UNIQUE,
                threshold_value REAL NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                updated_at TEXT NOT NULL
            )
            """
        )

        # -- Legacy tables kept for backward compatibility -------------------
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS finance_cards (
                id TEXT PRIMARY KEY,
                account_id TEXT,
                name TEXT NOT NULL,
                credit_limit_cents INTEGER NOT NULL,
                current_balance_cents INTEGER NOT NULL DEFAULT 0,
                minimum_payment_cents INTEGER NOT NULL DEFAULT 0,
                due_day INTEGER NOT NULL,
                statement_day INTEGER NOT NULL,
                autopay_enabled INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS finance_budget_categories (
                id TEXT PRIMARY KEY,
                budget_id TEXT NOT NULL,
                category TEXT NOT NULL,
                limit_cents INTEGER NOT NULL,
                warning_percent INTEGER NOT NULL DEFAULT 80
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS finance_savings_contributions (
                id TEXT PRIMARY KEY,
                goal_id TEXT NOT NULL,
                amount_cents INTEGER NOT NULL,
                ts TEXT NOT NULL,
                source TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS finance_holdings (
                id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                asset_type TEXT NOT NULL,
                quantity REAL NOT NULL,
                cost_basis_cents INTEGER NOT NULL,
                market_value_cents INTEGER NOT NULL,
                volatility_score REAL NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS finance_watchlist (
                id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                thesis TEXT,
                review_by TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS finance_recurring_expenses (
                id TEXT PRIMARY KEY,
                merchant TEXT NOT NULL,
                expected_amount_cents INTEGER NOT NULL,
                cadence_days INTEGER NOT NULL,
                last_seen_ts TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS finance_reminders (
                id TEXT PRIMARY KEY,
                reminder_type TEXT NOT NULL,
                entity_id TEXT,
                due_ts TEXT NOT NULL,
                message TEXT NOT NULL,
                acked INTEGER NOT NULL DEFAULT 0
            )
            """
        )

        # -- Auth domain -----------------------------------------------------
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bootstrap_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                bootstrapped INTEGER NOT NULL,
                admin_username TEXT NOT NULL,
                admin_password_hash TEXT NOT NULL,
                jwt_secret TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
        _DB_INITIALIZED.add(db_path)
    finally:
        conn.close()


def _ensure_columns(conn: sqlite3.Connection, table_name: str, columns: dict[str, str | None]) -> None:
    existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()}
    for column_name, column_sql in columns.items():
        if column_name not in existing and column_sql is not None:
            conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}")


def get_connection() -> sqlite3.Connection:
    init_db()
    conn = sqlite3.connect(str(get_db_path()))
    conn.row_factory = sqlite3.Row
    return conn
