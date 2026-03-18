from __future__ import annotations

from typing import Any

from core.finance.schemas import TransactionListFilters, TransactionWrite
from core.finance.service import add_transaction, list_transactions


def add_transaction_handler(parameters: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    payload = TransactionWrite(
        amount=parameters.get("amount"),
        currency=str(parameters.get("currency") or "USD"),
        category=str(parameters.get("category") or "uncategorized"),
        merchant=parameters.get("merchant"),
        note=parameters.get("note"),
        method=parameters.get("method"),
        account_id=parameters.get("account_id"),
        transaction_date=parameters.get("occurred_at") or parameters.get("transaction_date"),
        source=str(context.get("user_id") or "user"),
    )
    transaction_id = add_transaction(
        amount_cents=payload.amount_cents,
        currency=payload.currency,
        category=payload.category,
        merchant=payload.merchant,
        note=payload.note,
        method=payload.method,
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
    )
    results = list_transactions(
        start_ts=filters.date_from.isoformat() if filters.date_from else None,
        end_ts=filters.date_to.isoformat() if filters.date_to else None,
        category=filters.category,
        account_id=filters.account_id,
        limit=filters.limit,
    )
    return {"transactions": results, "count": len(results)}
