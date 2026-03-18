from __future__ import annotations

from typing import Any

from core.finance.schemas import (
    AccountCreate,
    BillCreate,
    BudgetCreate,
    SavingsGoalCreate,
    SavingsProgressUpdate,
    SpendingSummaryRequest,
    TransactionListFilters,
    TransactionWrite,
)
from core.finance.service import (
    FinanceService,
    add_transaction,
    category_summary,
    list_transactions,
    spending_summary,
)


_service = FinanceService()


# ---------------------------------------------------------------------------
# Ledger
# ---------------------------------------------------------------------------

def add_transaction_handler(parameters: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    payload = TransactionWrite(
        amount=parameters.get("amount"),
        currency=str(parameters.get("currency") or "USD"),
        category=str(parameters.get("category") or "uncategorized"),
        merchant=parameters.get("merchant"),
        notes=parameters.get("note") or parameters.get("notes"),
        payment_method=parameters.get("method") or parameters.get("payment_method"),
        account_id=parameters.get("account_id"),
        transaction_date=parameters.get("occurred_at") or parameters.get("transaction_date"),
        source=str(context.get("user_id") or "user"),
        direction=parameters.get("direction", "expense"),
        tags=parameters.get("tags"),
    )
    transaction_id = add_transaction(
        amount_cents=payload.amount_cents,
        currency=payload.currency,
        category=payload.category,
        merchant=payload.merchant,
        note=payload.notes,
        method=payload.payment_method,
        ts=payload.transaction_date.isoformat(),
        source=payload.source,
        account_id=payload.account_id,
    )
    return {
        "transaction_id": transaction_id,
        "message": f"Recorded {payload.currency} {payload.amount_cents / 100:.2f} transaction.",
        "ui_hints": {"card_type": "finance_confirmation", "priority": "normal", "expandable": True},
        "tone_hints": {"mode": "neutral_productivity"},
    }


def list_transactions_handler(parameters: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    _ = context
    filters = TransactionListFilters(
        category=parameters.get("category"),
        account_id=parameters.get("account_id"),
        date_from=parameters.get("date_from"),
        date_to=parameters.get("date_to"),
        limit=parameters.get("limit", 50),
        direction=parameters.get("direction"),
        merchant=parameters.get("merchant"),
    )
    results = list_transactions(
        start_ts=filters.date_from.isoformat() if filters.date_from else None,
        end_ts=filters.date_to.isoformat() if filters.date_to else None,
        category=filters.category,
        account_id=filters.account_id,
        limit=filters.limit,
    )
    return {"transactions": results, "count": len(results)}


def get_spending_summary_handler(parameters: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    _ = context
    result = spending_summary(
        date_from=parameters["date_from"],
        date_to=parameters["date_to"],
        account_id=parameters.get("account_id"),
    )
    return {"summary": result, "message": "Spending summary generated."}


def get_category_summary_handler(parameters: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    _ = context
    result = category_summary(
        date_from=parameters["date_from"],
        date_to=parameters["date_to"],
        account_id=parameters.get("account_id"),
    )
    return {"summary": result, "message": "Category summary generated."}


# ---------------------------------------------------------------------------
# Accounts
# ---------------------------------------------------------------------------

def create_account_handler(parameters: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    _ = context
    payload = AccountCreate(**parameters)
    response = _service.create_account(payload)
    return {"account": response.model_dump()["account"], "message": f"Account '{payload.name}' created."}


def list_accounts_handler(parameters: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    _ = parameters, context
    response = _service.list_accounts()
    return {"accounts": [a.model_dump() for a in response.results], "count": response.count}


# ---------------------------------------------------------------------------
# Budgets
# ---------------------------------------------------------------------------

def create_budget_handler(parameters: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    _ = context
    payload = BudgetCreate(**parameters)
    response = _service.create_budget(payload)
    return {"budget": response.model_dump()["budget"], "message": f"Budget '{payload.name}' created."}


def list_budgets_handler(parameters: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    _ = parameters, context
    response = _service.list_budgets()
    return {"budgets": [b.model_dump() for b in response.results], "count": response.count}


def get_budget_status_handler(parameters: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    _ = parameters, context
    response = _service.get_budget_status()
    return {"budget_status": [s.model_dump() for s in response.results], "count": response.count}


# ---------------------------------------------------------------------------
# Bills
# ---------------------------------------------------------------------------

def create_bill_handler(parameters: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    _ = context
    payload = BillCreate(**parameters)
    response = _service.create_bill(payload)
    return {"bill": response.model_dump()["bill"], "message": f"Bill '{payload.name}' created."}


def list_bills_handler(parameters: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    _ = parameters, context
    response = _service.list_bills()
    return {"bills": [b.model_dump() for b in response.results], "count": response.count}


def get_due_bills_handler(parameters: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    _ = parameters, context
    response = _service.get_due_bills()
    return {"due_bills": [b.model_dump() for b in response.results], "count": response.count}


def mark_bill_paid_handler(parameters: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    _ = context
    bill_id = parameters["bill_id"]
    response = _service.mark_bill_paid(bill_id)
    return {"bill": response.model_dump()["bill"], "message": "Bill marked as paid."}


# ---------------------------------------------------------------------------
# Savings
# ---------------------------------------------------------------------------

def create_savings_goal_handler(parameters: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    _ = context
    payload = SavingsGoalCreate(**parameters)
    response = _service.create_savings_goal(payload)
    return {"goal": response.model_dump()["goal"], "message": f"Savings goal '{payload.name}' created."}


def list_savings_goals_handler(parameters: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    _ = parameters, context
    response = _service.list_savings_goals()
    return {"goals": [g.model_dump() for g in response.results], "count": response.count}


def get_savings_status_handler(parameters: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    _ = parameters, context
    response = _service.get_savings_status()
    return {"savings_status": [s.model_dump() for s in response.results], "count": response.count}


# ---------------------------------------------------------------------------
# Alerts & Insights
# ---------------------------------------------------------------------------

def list_alerts_handler(parameters: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    _ = context
    limit = parameters.get("limit", 100)
    response = _service.list_alerts(limit=limit)
    return {"alerts": [a.model_dump() for a in response.results], "count": response.count}


def get_insights_handler(parameters: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    _ = context
    response = _service.get_insights(
        date_from=parameters["date_from"],
        date_to=parameters["date_to"],
    )
    return {"insights": [i.model_dump() for i in response.results], "date_from": response.date_from, "date_to": response.date_to}


def get_guidance_handler(parameters: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    _ = parameters, context
    response = _service.get_guidance()
    return {"guidance": [g.model_dump() for g in response.results], "count": response.count}
