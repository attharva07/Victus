from __future__ import annotations

from core.errors import VictusError


# ---------------------------------------------------------------------------
# Locked action surface — Section 6 of the Finance Domain spec
# ---------------------------------------------------------------------------

ALLOWED_FINANCE_ACTIONS = {
    # Ledger
    "add_transaction",
    "update_transaction",
    "delete_transaction",
    "get_transaction",
    "list_transactions",
    "get_spending_summary",
    "get_category_summary",
    "get_account_summary",
    # Accounts
    "create_account",
    "update_account",
    "list_accounts",
    "get_account",
    # Categories
    "list_categories",
    "create_category",
    "update_category",
    # Budgets
    "create_budget",
    "update_budget",
    "delete_budget",
    "list_budgets",
    "get_budget_status",
    # Bills / reminders
    "create_bill",
    "update_bill",
    "delete_bill",
    "list_bills",
    "mark_bill_paid",
    "get_due_bills",
    # Savings
    "create_savings_goal",
    "update_savings_goal",
    "list_savings_goals",
    "get_savings_status",
    "record_savings_progress",
    # Alerts / insights
    "list_alerts",
    "resolve_alert",
    "detect_recurring_expenses",
    "detect_anomalies",
    "get_insights",
    "get_guidance",
    # Intelligence
    "generate_brief",
    # Rules
    "set_rule_threshold",
    "get_rule_thresholds",
    # Legacy compat
    "spending_summary",
    "category_summary",
    "upsert_account",
    "create_transaction",
}


# ---------------------------------------------------------------------------
# Sensitive operations requiring stricter audit
# ---------------------------------------------------------------------------

SENSITIVE_ACTIONS = {
    "delete_transaction",
    "update_transaction",
    "delete_budget",
    "delete_bill",
}


class FinancePolicyError(VictusError):
    def __init__(self, message: str, *, code: str = "finance_policy_denied") -> None:
        super().__init__(message=message, safe_message="Finance action denied.", code=code)


class FinanceValidationError(VictusError):
    def __init__(self, message: str, *, code: str = "finance_validation_failed") -> None:
        super().__init__(message=message, safe_message="Invalid finance input.", code=code)


class FinanceNotFoundError(VictusError):
    def __init__(self, message: str, *, code: str = "finance_not_found") -> None:
        super().__init__(message=message, safe_message="Finance record not found.", code=code)


class FinanceConflictError(VictusError):
    def __init__(self, message: str, *, code: str = "finance_conflict") -> None:
        super().__init__(message=message, safe_message="Finance record conflict.", code=code)


def enforce_policy(action: str) -> None:
    if action not in ALLOWED_FINANCE_ACTIONS:
        raise FinancePolicyError(f"Unsupported finance action '{action}'")


def is_sensitive_action(action: str) -> bool:
    return action in SENSITIVE_ACTIONS
