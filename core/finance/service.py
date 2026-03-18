from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from core.finance import store
from core.finance.audit import finance_audit
from core.finance.intelligence import (
    DEFAULT_RULES,
    FinanceCognition,
    FinanceRecommendationEngine,
    FinanceReportingEngine,
    FinanceRuleConfig,
    FinanceRuleEngine,
)
from core.finance.policy import FinanceNotFoundError, FinanceValidationError, enforce_policy
from core.finance.repository import FinanceRepository
from core.finance.schemas import (
    AccountResponse,
    AccountUpsert,
    CategorySummary,
    LegacySummaryReport,
    SpendingSummary,
    SpendingSummaryRequest,
    SummaryTotals,
    TransactionListFilters,
    TransactionRecord,
    TransactionResponse,
    TransactionUpdate,
    TransactionWrite,
    TransactionsResponse,
)

DEFAULT_RULE_THRESHOLDS: dict[str, float] = {
    "credit_utilization_caution": DEFAULT_RULES.credit_utilization_caution,
    "credit_utilization_urgent": DEFAULT_RULES.credit_utilization_urgent,
    "due_soon_days": float(DEFAULT_RULES.due_soon_days),
    "statement_soon_days": float(DEFAULT_RULES.statement_soon_days),
    "budget_category_warning_percent": DEFAULT_RULES.budget_category_warning_percent,
    "budget_monthly_shortfall_percent": DEFAULT_RULES.budget_monthly_shortfall_percent,
    "recurring_min_occurrences": float(DEFAULT_RULES.recurring_min_occurrences),
    "portfolio_concentration_caution": DEFAULT_RULES.portfolio_concentration_caution,
    "volatility_alert_threshold": DEFAULT_RULES.volatility_alert_threshold,
}


class LedgerCoreService:
    def __init__(self, repository: FinanceRepository | None = None) -> None:
        self.repository = repository or FinanceRepository()

    def upsert_account(self, payload: AccountUpsert) -> AccountResponse:
        enforce_policy("upsert_account")
        account = self.repository.upsert_account(
            account_id=payload.id,
            name=payload.name,
            account_type=payload.account_type,
            institution=payload.institution,
            is_active=payload.is_active,
        )
        finance_audit(
            "finance_account_upserted",
            account_id=account.id,
            account_type=account.account_type,
            institution=account.institution,
            is_active=account.is_active,
        )
        return AccountResponse(account=account.__dict__)

    def create_transaction(self, payload: TransactionWrite) -> TransactionResponse:
        enforce_policy("create_transaction")
        if payload.account_id and self.repository.get_account(payload.account_id) is None:
            raise FinanceValidationError(f"Unknown account_id '{payload.account_id}'")
        self.repository.create_or_get_category(payload.category)
        now = _utc_now_iso()
        record = {
            "id": str(uuid4()),
            "ts": now,
            "transaction_date": payload.transaction_date.isoformat(),
            "amount_cents": payload.amount_cents,
            "currency": payload.currency,
            "category": payload.category,
            "merchant": payload.merchant,
            "note": payload.note,
            "account_id": payload.account_id,
            "method": payload.method,
            "source": payload.source,
            "created_at": now,
            "updated_at": now,
        }
        transaction = self.repository.create_transaction(record)
        finance_audit(
            "finance_transaction_created",
            transaction_id=transaction.id,
            amount_cents=transaction.amount_cents,
            currency=transaction.currency,
            category=transaction.category,
            account_id=transaction.account_id,
            merchant=transaction.merchant,
            note=transaction.note,
            method=transaction.method,
            source=transaction.source,
        )
        return TransactionResponse(transaction=_to_transaction_record(transaction))

    def get_transaction(self, transaction_id: str) -> TransactionResponse:
        enforce_policy("get_transaction")
        transaction = self.repository.get_transaction(transaction_id)
        if transaction is None:
            raise FinanceNotFoundError(f"Transaction '{transaction_id}' was not found")
        finance_audit("finance_transaction_read", transaction_id=transaction_id)
        return TransactionResponse(transaction=_to_transaction_record(transaction))

    def update_transaction(self, transaction_id: str, payload: TransactionUpdate) -> TransactionResponse:
        enforce_policy("update_transaction")
        existing = self.repository.get_transaction(transaction_id)
        if existing is None:
            raise FinanceNotFoundError(f"Transaction '{transaction_id}' was not found")
        if payload.account_id and self.repository.get_account(payload.account_id) is None:
            raise FinanceValidationError(f"Unknown account_id '{payload.account_id}'")
        updates: dict[str, Any] = {"updated_at": _utc_now_iso()}
        if payload.amount is not None:
            updates["amount_cents"] = payload.amount_cents
        if payload.currency is not None:
            updates["currency"] = payload.currency
        if payload.category is not None:
            self.repository.create_or_get_category(payload.category)
            updates["category"] = payload.category
        if "merchant" in payload.model_fields_set:
            updates["merchant"] = payload.merchant
        if "note" in payload.model_fields_set:
            updates["note"] = payload.note
        if "account_id" in payload.model_fields_set:
            updates["account_id"] = payload.account_id
        if "method" in payload.model_fields_set:
            updates["method"] = payload.method
        if payload.transaction_date is not None:
            updates["transaction_date"] = payload.transaction_date.isoformat()
        transaction = self.repository.update_transaction(transaction_id, updates)
        if transaction is None:
            raise FinanceNotFoundError(f"Transaction '{transaction_id}' was not found")
        finance_audit(
            "finance_transaction_updated",
            transaction_id=transaction_id,
            changed_fields=sorted(updates.keys()),
            note=payload.note if "note" in payload.model_fields_set else None,
        )
        return TransactionResponse(transaction=_to_transaction_record(transaction))

    def delete_transaction(self, transaction_id: str) -> dict[str, Any]:
        enforce_policy("delete_transaction")
        deleted = self.repository.delete_transaction(transaction_id)
        finance_audit("finance_transaction_deleted", transaction_id=transaction_id, deleted=deleted)
        if not deleted:
            raise FinanceNotFoundError(f"Transaction '{transaction_id}' was not found")
        return {"deleted": True, "transaction_id": transaction_id}

    def list_transactions(self, filters: TransactionListFilters) -> TransactionsResponse:
        enforce_policy("list_transactions")
        results = self.repository.list_transactions(
            date_from=filters.date_from.isoformat() if isinstance(filters.date_from, date) else None,
            date_to=filters.date_to.isoformat() if isinstance(filters.date_to, date) else None,
            category=filters.category,
            account_id=filters.account_id,
            limit=filters.limit,
        )
        finance_audit(
            "finance_transactions_listed",
            date_from=filters.date_from.isoformat() if isinstance(filters.date_from, date) else None,
            date_to=filters.date_to.isoformat() if isinstance(filters.date_to, date) else None,
            category=filters.category,
            account_id=filters.account_id,
            limit=filters.limit,
            result_count=len(results),
        )
        return TransactionsResponse(results=[_to_transaction_record(item) for item in results], count=len(results))

    def spending_summary(self, request: SpendingSummaryRequest) -> SpendingSummary:
        enforce_policy("spending_summary")
        snapshot = self.repository.summarize_spending(
            date_from=request.date_from.isoformat(),
            date_to=request.date_to.isoformat(),
            account_id=request.account_id,
        )
        currency = snapshot["transactions"][0].currency if snapshot["transactions"] else "USD"
        response = SpendingSummary(
            date_from=request.date_from.isoformat(),
            date_to=request.date_to.isoformat(),
            account_id=request.account_id,
            totals=SummaryTotals(
                currency=currency,
                income_cents=snapshot["income_cents"],
                expense_cents=snapshot["expense_cents"],
                net_cents=snapshot["net_cents"],
                transaction_count=len(snapshot["transactions"]),
            ),
            by_category=snapshot["by_category"],
            by_account=snapshot["by_account"],
        )
        finance_audit(
            "finance_spending_summary_generated",
            date_from=response.date_from,
            date_to=response.date_to,
            account_id=response.account_id,
            expense_cents=response.totals.expense_cents,
        )
        return response

    def category_summary(self, request: SpendingSummaryRequest) -> CategorySummary:
        enforce_policy("category_summary")
        spending = self.spending_summary(request)
        categories = [
            {"category": category, "expense_cents": amount}
            for category, amount in sorted(spending.by_category.items(), key=lambda item: (-item[1], item[0]))
        ]
        finance_audit(
            "finance_category_summary_generated",
            date_from=spending.date_from,
            date_to=spending.date_to,
            account_id=spending.account_id,
            category_count=len(categories),
        )
        return CategorySummary(
            date_from=spending.date_from,
            date_to=spending.date_to,
            account_id=spending.account_id,
            categories=categories,
        )


_LEDGER_SERVICE = LedgerCoreService()


def _utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _period_bounds(period: str, start_ts: str | None, end_ts: str | None) -> tuple[str | None, str | None]:
    now = datetime.now(tz=timezone.utc)
    if period == "week":
        start = now - timedelta(days=7)
        return start.isoformat(), now.isoformat()
    if period == "month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return start.isoformat(), now.isoformat()
    if period == "custom":
        return start_ts, end_ts
    return None, None


def _load_rule_config() -> FinanceRuleConfig:
    configured = store.list_rules()
    merged = {**DEFAULT_RULE_THRESHOLDS}
    for key, value in configured.items():
        if value.get("enabled", True):
            merged[key] = float(value["threshold_value"])
    return FinanceRuleConfig(
        credit_utilization_caution=float(merged["credit_utilization_caution"]),
        credit_utilization_urgent=float(merged["credit_utilization_urgent"]),
        due_soon_days=int(merged["due_soon_days"]),
        statement_soon_days=int(merged["statement_soon_days"]),
        budget_category_warning_percent=float(merged["budget_category_warning_percent"]),
        budget_monthly_shortfall_percent=float(merged["budget_monthly_shortfall_percent"]),
        recurring_min_occurrences=int(merged["recurring_min_occurrences"]),
        portfolio_concentration_caution=float(merged["portfolio_concentration_caution"]),
        volatility_alert_threshold=float(merged["volatility_alert_threshold"]),
    )


# Backward-compatible entry points used by current app/orchestrator code.
def add_transaction(
    amount_cents: int,
    currency: str = "USD",
    category: str = "uncategorized",
    merchant: str | None = None,
    note: str | None = None,
    method: str | None = None,
    ts: str | None = None,
    source: str = "user",
    account_id: str | None = None,
) -> str:
    transaction_date = _coerce_ts_to_date(ts)
    response = _LEDGER_SERVICE.create_transaction(
        TransactionWrite(
            amount=amount_cents / 100,
            currency=currency,
            category=category,
            merchant=merchant,
            note=note,
            method=method,
            source=source,
            account_id=account_id,
            transaction_date=transaction_date,
        )
    )
    return response.transaction.id


def get_transaction(transaction_id: str) -> dict[str, Any]:
    return _LEDGER_SERVICE.get_transaction(transaction_id).model_dump()["transaction"]


def update_transaction(transaction_id: str, **updates: Any) -> dict[str, Any]:
    payload = TransactionUpdate(**updates)
    return _LEDGER_SERVICE.update_transaction(transaction_id, payload).model_dump()["transaction"]


def delete_transaction(transaction_id: str) -> dict[str, Any]:
    return _LEDGER_SERVICE.delete_transaction(transaction_id)


def upsert_account(**kwargs: Any) -> dict[str, Any]:
    response = _LEDGER_SERVICE.upsert_account(AccountUpsert(**kwargs))
    return response.model_dump()["account"]


def list_transactions(
    start_ts: str | None = None,
    end_ts: str | None = None,
    category: str | None = None,
    limit: int = 50,
    account_id: str | None = None,
) -> list[dict[str, Any]]:
    filters = TransactionListFilters(
        date_from=_coerce_ts_to_date(start_ts) if start_ts else None,
        date_to=_coerce_ts_to_date(end_ts) if end_ts else None,
        category=category,
        account_id=account_id,
        limit=limit,
    )
    return _LEDGER_SERVICE.list_transactions(filters).model_dump()["results"]


def spending_summary(date_from: str, date_to: str, account_id: str | None = None) -> dict[str, Any]:
    request = SpendingSummaryRequest(date_from=date_from, date_to=date_to, account_id=account_id)
    return _LEDGER_SERVICE.spending_summary(request).model_dump()


def category_summary(date_from: str, date_to: str, account_id: str | None = None) -> dict[str, Any]:
    request = SpendingSummaryRequest(date_from=date_from, date_to=date_to, account_id=account_id)
    return _LEDGER_SERVICE.category_summary(request).model_dump()


def summary(
    period: str = "week",
    start_ts: str | None = None,
    end_ts: str | None = None,
    group_by: str = "category",
) -> dict[str, Any]:
    start, end = _period_bounds(period, start_ts, end_ts)
    if start is None or end is None:
        raise FinanceValidationError(f"Unsupported period '{period}'")
    items = _LEDGER_SERVICE.list_transactions(
        TransactionListFilters(
            date_from=_coerce_ts_to_date(start),
            date_to=_coerce_ts_to_date(end),
            limit=500,
        )
    ).results
    totals: dict[str, int] = {}
    for item in items:
        if group_by == "category":
            key = item.category
        else:
            key = getattr(item, group_by, None) or "unknown"
        totals[key] = totals.get(key, 0) + item.amount_cents
    report = LegacySummaryReport(
        period=period,
        start_ts=start,
        end_ts=end,
        group_by=group_by,
        totals=totals,
    )
    finance_audit(
        "finance_summary_requested",
        period=period,
        start_ts=start,
        end_ts=end,
        group_by=group_by,
    )
    return report.model_dump()


def set_rule_threshold(rule_key: str, threshold_value: float, enabled: bool = True) -> dict[str, Any]:
    if rule_key not in DEFAULT_RULE_THRESHOLDS:
        raise ValueError(f"Unsupported rule '{rule_key}'")
    updated_at = _utc_now_iso()
    store.upsert_rule(rule_key, threshold_value, enabled, updated_at)
    finance_audit("finance_rule_threshold_set", rule_key=rule_key, threshold_value=threshold_value, enabled=enabled)
    return {"rule_key": rule_key, "threshold_value": threshold_value, "enabled": enabled, "updated_at": updated_at}


def get_rule_thresholds() -> dict[str, dict[str, Any]]:
    configured = store.list_rules()
    output: dict[str, dict[str, Any]] = {}
    for key, default in DEFAULT_RULE_THRESHOLDS.items():
        if key in configured:
            output[key] = configured[key]
        else:
            output[key] = {"threshold_value": default, "enabled": True}
    return output


def generate_finance_brief(snapshot: dict[str, Any], now: datetime | None = None) -> dict[str, Any]:
    transactions = snapshot.get("transactions") or []
    cognition = FinanceCognition()
    insights = cognition.analyze(transactions, paycheck_days=snapshot.get("paycheck_days"))
    recurring = cognition.detect_recurring_expenses(transactions)

    engine = FinanceRuleEngine(config=_load_rule_config())
    alerts = engine.evaluate(snapshot, now=now)
    recommendation_engine = FinanceRecommendationEngine()
    recommendations = recommendation_engine.generate(alerts, insights)

    report_engine = FinanceReportingEngine()
    daily_brief = report_engine.daily_brief(snapshot, alerts, recommendations)
    weekly = report_engine.weekly_summary(transactions, insights)

    for alert in alerts:
        store.add_alert(
            {
                "id": str(uuid4()),
                "severity": alert["severity"],
                "title": alert["title"],
                "message": alert["message"],
                "reason": alert["reason"],
                "entity_type": alert.get("entity_type"),
                "entity_id": alert.get("entity_id"),
                "suggested_next_step": alert.get("suggested_next_step"),
                "ts": alert["timestamp"],
            }
        )
    for insight in insights:
        store.add_behavior_log(
            {
                "id": str(uuid4()),
                "behavior_type": insight["pattern"],
                "score": float(insight["score"]),
                "details": insight,
                "ts": _utc_now_iso(),
            }
        )

    finance_audit(
        "finance_intelligence_brief_generated",
        alert_count=len(alerts),
        recommendation_count=len(recommendations),
        recurring_count=len(recurring),
        insight_count=len(insights),
    )
    return {
        "daily_brief": daily_brief,
        "weekly_summary": weekly,
        "alerts": alerts,
        "recommendations": recommendations,
        "recurring_expenses": recurring,
        "behavior_insights": insights,
    }


def list_alerts(limit: int = 100) -> list[dict[str, Any]]:
    return store.list_alerts(limit=limit)


def list_behavior_logs(limit: int = 100) -> list[dict[str, Any]]:
    return store.list_behavior_logs(limit=limit)


def _to_transaction_record(item: Any) -> TransactionRecord:
    return TransactionRecord(**item.__dict__)


def _coerce_ts_to_date(value: str | None) -> str:
    if not value:
        return datetime.now(tz=timezone.utc).date().isoformat()
    candidate = str(value)
    if len(candidate) >= 10:
        try:
            return datetime.fromisoformat(candidate.replace("Z", "+00:00")).date().isoformat()
        except ValueError:
            pass
        try:
            return date.fromisoformat(candidate[:10]).isoformat()
        except ValueError as exc:
            raise FinanceValidationError(f"Invalid timestamp/date '{value}'") from exc
    raise FinanceValidationError(f"Invalid timestamp/date '{value}'")
