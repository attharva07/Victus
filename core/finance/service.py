from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from core.finance import store
from core.finance.intelligence import (
    DEFAULT_RULES,
    FinanceCognition,
    FinanceRecommendationEngine,
    FinanceReportingEngine,
    FinanceRuleConfig,
    FinanceRuleEngine,
)
from core.logging.audit import audit_event


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


def add_transaction(
    amount_cents: int,
    currency: str = "USD",
    category: str = "uncategorized",
    merchant: str | None = None,
    note: str | None = None,
    method: str | None = None,
    ts: str | None = None,
    source: str = "user",
) -> str:
    ts_value = ts or datetime.now(tz=timezone.utc).isoformat()
    transaction_id = str(uuid4())
    record = {
        "id": transaction_id,
        "ts": ts_value,
        "amount_cents": amount_cents,
        "currency": currency,
        "category": category,
        "merchant": merchant,
        "note": note,
        "method": method,
        "source": source,
    }
    store.add_transaction(record)
    audit_event(
        "finance_transaction_added",
        transaction_id=transaction_id,
        amount_cents=amount_cents,
        currency=currency,
        category=category,
        merchant=merchant,
        method=method,
        source=source,
    )
    return transaction_id


def list_transactions(
    start_ts: str | None = None,
    end_ts: str | None = None,
    category: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    results = store.list_transactions(start_ts, end_ts, category, limit)
    audit_event(
        "finance_transactions_listed",
        start_ts=start_ts,
        end_ts=end_ts,
        category=category,
        limit=limit,
    )
    return results


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


def summary(
    period: str = "week",
    start_ts: str | None = None,
    end_ts: str | None = None,
    group_by: str = "category",
) -> dict[str, Any]:
    start, end = _period_bounds(period, start_ts, end_ts)
    totals = store.summarize_transactions(start, end, group_by)
    report = {"period": period, "start_ts": start, "end_ts": end, "group_by": group_by, "totals": totals}
    audit_event(
        "finance_summary_requested",
        period=period,
        start_ts=start,
        end_ts=end,
        group_by=group_by,
    )
    return report


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


def set_rule_threshold(rule_key: str, threshold_value: float, enabled: bool = True) -> dict[str, Any]:
    if rule_key not in DEFAULT_RULE_THRESHOLDS:
        raise ValueError(f"Unsupported rule '{rule_key}'")
    updated_at = datetime.now(tz=timezone.utc).isoformat()
    store.upsert_rule(rule_key, threshold_value, enabled, updated_at)
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
                "ts": datetime.now(tz=timezone.utc).isoformat(),
            }
        )

    audit_event(
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
