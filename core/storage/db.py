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
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY,
                ts TEXT,
                amount_cents INTEGER,
                currency TEXT,
                category TEXT,
                merchant TEXT,
                note TEXT,
                method TEXT,
                source TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS finance_accounts (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                account_type TEXT NOT NULL,
                institution TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            )
            """
        )
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
            CREATE TABLE IF NOT EXISTS finance_budgets (
                id TEXT PRIMARY KEY,
                month TEXT NOT NULL,
                total_limit_cents INTEGER NOT NULL,
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
            CREATE TABLE IF NOT EXISTS finance_savings_goals (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                target_cents INTEGER NOT NULL,
                target_date TEXT,
                monthly_contribution_cents INTEGER NOT NULL,
                current_cents INTEGER NOT NULL DEFAULT 0,
                is_emergency_fund INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL
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
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS finance_alerts (
                id TEXT PRIMARY KEY,
                severity TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                reason TEXT NOT NULL,
                entity_type TEXT,
                entity_id TEXT,
                suggested_next_step TEXT,
                ts TEXT NOT NULL,
                acked INTEGER NOT NULL DEFAULT 0
            )
            """
        )
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


def get_connection() -> sqlite3.Connection:
    init_db()
    conn = sqlite3.connect(str(get_db_path()))
    conn.row_factory = sqlite3.Row
    return conn
