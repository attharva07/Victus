from __future__ import annotations

from typing import Any, Optional

from core.finance.service import category_summary, spending_summary
from core.finance.service import add_transaction as core_add_transaction
from core.finance.service import list_transactions as core_list_transactions
from core.finance.service import summary as core_summary


def _month_range(month: str) -> tuple[str, str]:
    year, month_part = month.split("-")
    month_int = int(month_part)
    if month_int == 12:
        return f"{month}-01", f"{int(year) + 1}-01-01"
    return f"{month}-01", f"{year}-{month_int + 1:02d}-01"


def add_transaction(
    *,
    date: Optional[str],
    amount: float,
    category: str,
    merchant: Optional[str] = None,
    note: Optional[str] = None,
    account: Optional[str] = None,
    payment_method: Optional[str] = None,
    tags: Optional[str] = None,
    source: str = "manual",
) -> dict[str, Any]:
    transaction_id = core_add_transaction(
        amount_cents=int(round(amount * 100)),
        currency="USD",
        category=category,
        merchant=merchant,
        note=note,
        method=payment_method,
        ts=date,
        source=source,
        account_id=account,
    )
    transaction = next(item for item in core_list_transactions(limit=1_000) if item["id"] == transaction_id)
    transaction["tags"] = tags
    return transaction


def list_transactions(
    *,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    category: Optional[str] = None,
    account: Optional[str] = None,
) -> list[dict[str, Any]]:
    return core_list_transactions(start_ts=date_from, end_ts=date_to, category=category, account_id=account, limit=500)


def month_summary(month: Optional[str] = None) -> dict[str, Any]:
    if month is None:
        return core_summary(period="month", group_by="category")
    date_from, next_month = _month_range(month)
    spend = spending_summary(date_from, next_month, None)
    return {
        "month": month,
        "total_income": round(spend["totals"]["income_cents"] / 100, 2),
        "total_expense": round(-spend["totals"]["expense_cents"] / 100, 2),
        "net": round(spend["totals"]["net_cents"] / 100, 2),
        "by_category": {key: round(-value / 100, 2) for key, value in spend["by_category"].items()},
        "count": spend["totals"]["transaction_count"],
    }


def paycheck_plan(pay_date: str) -> dict[str, Any]:
    return {"pay_date": pay_date, "month": pay_date[:7], "planned_total": 0.0, "allocations": {}, "note": "Budget planning not yet configured in the consolidated ledger."}


def export_logbook_md(
    *,
    range: str = "month",
    month: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> str:
    if range == "month" and month:
        date_from, date_to = _month_range(month)
    if not date_from or not date_to:
        raise ValueError("date range is required")
    items = list_transactions(date_from=date_from, date_to=date_to)
    categories = category_summary(date_from, date_to)
    lines = ["# Finance Logbook", "", f"Range: {range}", f"Dates: {date_from} → {date_to}", "", "## Transactions", "", "| Date | Amount | Category | Merchant | Note | Account |", "| --- | ---: | --- | --- | --- | --- |"]
    for tx in items:
        lines.append(
            f"| {tx['transaction_date']} | {tx['amount_cents'] / 100:.2f} | {tx['category']} | {tx.get('merchant') or ''} | {(tx.get('note') or '')[:24]} | {tx.get('account_id') or ''} |"
        )
    lines.extend(["", "## Category totals"])
    for item in categories["categories"]:
        lines.append(f"- {item['category']}: {item['expense_cents'] / 100:.2f}")
    return "\n".join(lines) + "\n"
