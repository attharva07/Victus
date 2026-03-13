from __future__ import annotations

from typing import Any

from core.finance.service import add_transaction, list_transactions


def add_transaction_handler(parameters: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    amount = parameters.get("amount")
    merchant = parameters.get("merchant")
    if not isinstance(amount, (int, float)):
        raise ValueError("'amount' must be numeric")
    if not isinstance(merchant, str) or not merchant.strip():
        raise ValueError("'merchant' is required")

    amount_cents = int(round(float(amount) * 100))
    category = str(parameters.get("category") or "uncategorized")
    transaction_id = add_transaction(
        amount_cents=amount_cents,
        currency=str(parameters.get("currency") or "USD"),
        category=category,
        merchant=merchant.strip(),
        ts=parameters.get("occurred_at") if isinstance(parameters.get("occurred_at"), str) else None,
        source=str(context.get("user_id") or "user"),
    )
    return {
        "transaction_id": transaction_id,
        "message": f"Recorded ${amount_cents / 100:.2f} transaction at {merchant.strip()}.",
        "ui_hints": {"card_type": "finance_confirmation", "priority": "normal", "expandable": True},
        "tone_hints": {"mode": "neutral_productivity"},
    }


def list_transactions_handler(parameters: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    _ = context
    limit = parameters.get("limit", 50)
    if not isinstance(limit, int):
        raise ValueError("'limit' must be an integer")
    results = list_transactions(limit=limit, category=parameters.get("category"))
    return {"transactions": results, "count": len(results)}
