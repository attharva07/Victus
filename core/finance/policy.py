from __future__ import annotations

from core.errors import VictusError


ALLOWED_FINANCE_ACTIONS = {
    "create_transaction",
    "update_transaction",
    "delete_transaction",
    "get_transaction",
    "list_transactions",
    "spending_summary",
    "category_summary",
    "upsert_account",
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
