from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .db import get_connection, init_db


def _parse_month_range(month: str) -> tuple[str, str]:
    start = datetime.strptime(month + "-01", "%Y-%m-%d")
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1, day=1)
    else:
        end = start.replace(month=start.month + 1, day=1)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


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
) -> Dict[str, Any]:
    init_db()
    if not date:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO transactions (ts, date, amount, category, merchant, note, account, payment_method, tags, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (ts, date, amount, category, merchant, note, account, payment_method, tags, source),
    )
    connection.commit()
    transaction_id = cursor.lastrowid
    connection.close()
    return {
        "id": transaction_id,
        "ts": ts,
        "date": date,
        "amount": amount,
        "category": category,
        "merchant": merchant,
        "note": note,
        "account": account,
        "payment_method": payment_method,
        "tags": tags,
        "source": source,
    }


def list_transactions(
    *,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    category: Optional[str] = None,
    account: Optional[str] = None,
) -> List[Dict[str, Any]]:
    init_db()
    connection = get_connection()
    cursor = connection.cursor()
    query = "SELECT * FROM transactions WHERE 1=1"
    params: list[Any] = []
    if date_from:
        query += " AND date >= ?"
        params.append(date_from)
    if date_to:
        query += " AND date < ?"
        params.append(date_to)
    if category:
        query += " AND category = ?"
        params.append(category)
    if account:
        query += " AND account = ?"
        params.append(account)
    query += " ORDER BY date DESC, id DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    connection.close()
    return [dict(row) for row in rows]


def month_summary(month: Optional[str] = None) -> Dict[str, Any]:
    init_db()
    if month is None:
        month = datetime.now(timezone.utc).strftime("%Y-%m")
    date_from, date_to = _parse_month_range(month)
    transactions = list_transactions(date_from=date_from, date_to=date_to)
    total_income = sum(tx["amount"] for tx in transactions if tx["amount"] > 0)
    total_expense = sum(tx["amount"] for tx in transactions if tx["amount"] < 0)
    by_category: Dict[str, float] = defaultdict(float)
    for tx in transactions:
        by_category[tx["category"]] += tx["amount"]
    return {
        "month": month,
        "total_income": round(total_income, 2),
        "total_expense": round(total_expense, 2),
        "net": round(total_income + total_expense, 2),
        "by_category": dict(sorted(by_category.items(), key=lambda item: item[0].lower())),
        "count": len(transactions),
    }


def paycheck_plan(pay_date: str) -> Dict[str, Any]:
    init_db()
    connection = get_connection()
    cursor = connection.cursor()
    month = pay_date[:7]
    cursor.execute("SELECT category, limit_amount FROM budgets WHERE month = ?", (month,))
    budgets = cursor.fetchall()
    connection.close()
    allocation = {row["category"]: row["limit_amount"] for row in budgets}
    total_planned = sum(allocation.values())
    return {
        "pay_date": pay_date,
        "month": month,
        "planned_total": round(total_planned, 2),
        "allocations": allocation,
        "note": "Simple plan based on budget caps.",
    }


def export_logbook_md(
    *,
    range: str = "month",
    month: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> str:
    if range == "month":
        if month is None:
            month = datetime.now(timezone.utc).strftime("%Y-%m")
        date_from, date_to = _parse_month_range(month)
    transactions = list_transactions(date_from=date_from, date_to=date_to)
    summary = month_summary(month if range == "month" else None)

    lines = ["# Finance Logbook", "", f"Range: {range}"]
    if date_from and date_to:
        lines.append(f"Dates: {date_from} → {date_to}")
    if summary:
        lines.extend(
            [
                "",
                "## Summary",
                f"- Total income: {summary['total_income']}",
                f"- Total expense: {summary['total_expense']}",
                f"- Net: {summary['net']}",
                f"- Transactions: {summary['count']}",
            ]
        )

    lines.extend(["", "## Transactions", "", "| Date | Amount | Category | Merchant | Note | Account |",
                  "| --- | ---: | --- | --- | --- | --- |"]) 
    for tx in transactions:
        lines.append(
            "| {date} | {amount:.2f} | {category} | {merchant} | {note} | {account} |".format(
                date=tx["date"],
                amount=tx["amount"],
                category=tx["category"],
                merchant=tx.get("merchant") or "",
                note=tx.get("note") or "",
                account=tx.get("account") or "",
            )
        )

    if summary.get("by_category"):
        lines.append("")
        lines.append("## Category totals")
        for category, total in summary["by_category"].items():
            lines.append(f"- {category}: {total:.2f}")

    return "\n".join(lines) + "\n"
