from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from statistics import mean
from typing import Any


@dataclass
class FinanceRuleConfig:
    credit_utilization_caution: float = 0.3
    credit_utilization_urgent: float = 0.8
    due_soon_days: int = 3
    statement_soon_days: int = 4
    budget_category_warning_percent: float = 0.8
    budget_monthly_shortfall_percent: float = 1.0
    recurring_min_occurrences: int = 3
    recurring_tolerance_percent: float = 0.2
    savings_missed_months_threshold: int = 1
    portfolio_concentration_caution: float = 0.35
    volatility_alert_threshold: float = 0.75


DEFAULT_RULES = FinanceRuleConfig()


class FinanceRuleEngine:
    def __init__(self, config: FinanceRuleConfig | None = None) -> None:
        self.config = config or DEFAULT_RULES

    def evaluate(self, snapshot: dict[str, Any], now: datetime | None = None) -> list[dict[str, Any]]:
        current = now or datetime.now(tz=timezone.utc)
        alerts: list[dict[str, Any]] = []
        alerts.extend(self._credit_alerts(snapshot.get("cards", []), current))
        alerts.extend(self._budget_alerts(snapshot.get("budget", {}), snapshot.get("transactions", []), current))
        alerts.extend(self._savings_alerts(snapshot.get("savings_goals", []), current))
        alerts.extend(self._investment_alerts(snapshot.get("holdings", []), snapshot.get("watchlist", []), current))
        return alerts

    def _credit_alerts(self, cards: list[dict[str, Any]], now: datetime) -> list[dict[str, Any]]:
        alerts: list[dict[str, Any]] = []
        for card in cards:
            limit_cents = int(card.get("credit_limit_cents", 0))
            balance_cents = int(card.get("current_balance_cents", 0))
            if limit_cents <= 0:
                continue
            utilization = balance_cents / limit_cents
            due_days = int(card.get("due_in_days", 99))
            statement_days = int(card.get("statement_in_days", 99))
            if utilization >= self.config.credit_utilization_urgent:
                alerts.append(_alert("urgent", "High card utilization", f"{card['name']} utilization is {utilization:.0%}.", "credit_utilization_high", "card", card["id"], "Pay down balance before statement closes."))
            elif utilization >= self.config.credit_utilization_caution:
                alerts.append(_alert("caution", "Card utilization elevated", f"{card['name']} utilization is {utilization:.0%}.", "credit_utilization_caution", "card", card["id"], "Shift discretionary spend to debit or pay early."))
            if due_days <= self.config.due_soon_days:
                severity = "urgent" if due_days <= 1 and not card.get("autopay_enabled", False) else "advisory"
                alerts.append(_alert(severity, "Card due date approaching", f"{card['name']} due in {due_days} day(s).", "card_due_date", "card", card["id"], "Confirm payment coverage and autopay settings."))
            if statement_days <= self.config.statement_soon_days and utilization >= self.config.credit_utilization_caution:
                alerts.append(_alert("advisory", "Pre-statement utilization advice", f"{card['name']} statement closes in {statement_days} day(s) at {utilization:.0%} utilization.", "statement_close_warning", "card", card["id"], "Pay part of balance before close date."))
        return alerts

    def _budget_alerts(self, budget: dict[str, Any], transactions: list[dict[str, Any]], now: datetime) -> list[dict[str, Any]]:
        alerts: list[dict[str, Any]] = []
        category_spend: dict[str, int] = defaultdict(int)
        month_total_spend = 0
        for tx in transactions:
            amount = int(tx.get("amount_cents", 0))
            if amount < 0:
                spent = abs(amount)
                category_spend[str(tx.get("category", "uncategorized"))] += spent
                month_total_spend += spent

        categories = budget.get("categories", {})
        for category, limit in categories.items():
            limit_cents = int(limit)
            spent = category_spend.get(category, 0)
            if limit_cents <= 0:
                continue
            usage = spent / limit_cents
            if usage >= 1.0:
                alerts.append(_alert("urgent", "Category over budget", f"{category} is at {usage:.0%} of monthly cap.", "category_overspend", "budget_category", category, "Reduce variable spend in this category this week."))
            elif usage >= self.config.budget_category_warning_percent:
                alerts.append(_alert("caution", "Category nearing budget cap", f"{category} is at {usage:.0%} of monthly cap.", "category_threshold", "budget_category", category, "Pace spending to avoid end-of-month overrun."))

        total_limit_cents = int(budget.get("total_limit_cents", 0))
        day_of_month = max(now.day, 1)
        days_in_month = 30
        projected_spend = int(month_total_spend / day_of_month * days_in_month)
        if total_limit_cents > 0 and projected_spend > total_limit_cents * self.config.budget_monthly_shortfall_percent:
            alerts.append(_alert("caution", "Monthly shortfall predicted", f"Projected spend {projected_spend / 100:.2f} exceeds monthly budget {total_limit_cents / 100:.2f}.", "monthly_shortfall_prediction", "budget", budget.get("id", "monthly"), "Cut non-essential spend this week."))
        return alerts

    def _savings_alerts(self, goals: list[dict[str, Any]], now: datetime) -> list[dict[str, Any]]:
        alerts: list[dict[str, Any]] = []
        for goal in goals:
            monthly_target = int(goal.get("monthly_contribution_cents", 0))
            contributed = int(goal.get("contributed_this_month_cents", 0))
            if monthly_target > 0 and contributed < monthly_target:
                gap = monthly_target - contributed
                alerts.append(_alert("advisory", "Savings contribution behind plan", f"Goal {goal['name']} is short by {gap / 100:.2f} this month.", "savings_missed_pace", "savings_goal", goal["id"], "Increase weekly transfer pace to recover."))
            if goal.get("is_emergency_fund") and int(goal.get("current_cents", 0)) < int(goal.get("emergency_target_cents", 0)):
                alerts.append(_alert("info", "Emergency fund below target", f"{goal['name']} is not yet at target reserve.", "emergency_fund_awareness", "savings_goal", goal["id"], "Continue scheduled contributions until reserve target is reached."))
        return alerts

    def _investment_alerts(self, holdings: list[dict[str, Any]], watchlist: list[dict[str, Any]], now: datetime) -> list[dict[str, Any]]:
        alerts: list[dict[str, Any]] = []
        total_value = sum(int(item.get("market_value_cents", 0)) for item in holdings)
        if total_value > 0:
            for item in holdings:
                weight = int(item.get("market_value_cents", 0)) / total_value
                if weight >= self.config.portfolio_concentration_caution:
                    alerts.append(_alert("caution", "Portfolio concentration risk", f"{item['symbol']} is {weight:.0%} of portfolio.", "portfolio_concentration", "holding", item["id"], "Review allocation against risk tolerance."))
                if float(item.get("volatility_score", 0.0)) >= self.config.volatility_alert_threshold:
                    alerts.append(_alert("advisory", "Holding volatility alert", f"{item['symbol']} shows elevated volatility score.", "volatility_alert", "holding", item["id"], "Re-check thesis and position sizing."))
        for watch in watchlist:
            if watch.get("review_in_days", 999) <= 0:
                alerts.append(_alert("info", "Thesis review reminder", f"Watchlist symbol {watch['symbol']} is due for review.", "thesis_review_due", "watchlist", watch["id"], "Review thesis and keep/remove from watchlist."))
        return alerts


class FinanceCognition:
    """Lightweight, explainable pattern analysis for finance-only behavior."""

    def analyze(self, transactions: list[dict[str, Any]], paycheck_days: list[int] | None = None) -> list[dict[str, Any]]:
        insights: list[dict[str, Any]] = []
        if not transactions:
            return insights

        ordered = sorted(transactions, key=lambda item: str(item.get("ts", "")), reverse=True)
        expenses = [abs(int(tx["amount_cents"])) for tx in ordered if int(tx.get("amount_cents", 0)) < 0]
        if expenses:
            avg = mean(expenses)
            latest = expenses[0]
            if latest > avg * 1.6:
                insights.append({"pattern": "spending_drift", "score": round(latest / max(avg, 1), 2), "reason": "Latest expense is significantly above baseline average.", "suggestion": "Review recent discretionary purchases and rebalance this week."})

        merchant_counts: dict[str, int] = defaultdict(int)
        for tx in transactions:
            merchant = (tx.get("merchant") or "").strip().lower()
            if merchant:
                merchant_counts[merchant] += 1
        frequent = [m for m, c in merchant_counts.items() if c >= 4]
        if frequent:
            insights.append({"pattern": "repeated_merchant_habit", "score": float(len(frequent)), "reason": f"Repeated spending found across {len(frequent)} merchants.", "suggestion": "Set merchant-level spending caps for top recurring discretionary merchants."})

        if paycheck_days:
            payday_spend = 0
            non_payday_spend = 0
            for tx in transactions:
                amount = int(tx.get("amount_cents", 0))
                if amount >= 0:
                    continue
                day = _day_of_month(str(tx.get("ts", "")))
                if day in paycheck_days:
                    payday_spend += abs(amount)
                else:
                    non_payday_spend += abs(amount)
            if payday_spend > non_payday_spend * 0.6 and payday_spend > 0:
                insights.append({"pattern": "post_payday_spike", "score": round(payday_spend / max(non_payday_spend, 1), 2), "reason": "High share of spend occurs on known payday dates.", "suggestion": "Use a 48-hour cooling rule for discretionary purchases after payday."})
        return insights

    def detect_recurring_expenses(self, transactions: list[dict[str, Any]], min_occurrences: int = 3) -> list[dict[str, Any]]:
        by_merchant: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for tx in transactions:
            amount = int(tx.get("amount_cents", 0))
            merchant = (tx.get("merchant") or "").strip().lower()
            if amount < 0 and merchant:
                by_merchant[merchant].append(tx)

        recurring: list[dict[str, Any]] = []
        for merchant, txs in by_merchant.items():
            if len(txs) < min_occurrences:
                continue
            amounts = [abs(int(tx["amount_cents"])) for tx in txs]
            avg_amount = int(mean(amounts))
            recurring.append({"merchant": merchant, "occurrences": len(txs), "expected_amount_cents": avg_amount, "cadence_days": 30})
        return sorted(recurring, key=lambda item: item["occurrences"], reverse=True)


class FinanceRecommendationEngine:
    def generate(self, alerts: list[dict[str, Any]], insights: list[dict[str, Any]]) -> list[dict[str, Any]]:
        recommendations: list[dict[str, Any]] = []
        for alert in alerts:
            recommendations.append({"title": alert["title"], "message": alert["suggested_next_step"], "source": alert["reason"], "severity": alert["severity"]})
        for insight in insights:
            recommendations.append({"title": insight["pattern"].replace("_", " ").title(), "message": insight["suggestion"], "source": insight["pattern"], "severity": "advisory"})
        return recommendations


class FinanceReportingEngine:
    def daily_brief(self, snapshot: dict[str, Any], alerts: list[dict[str, Any]], recommendations: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "generated_at": datetime.now(tz=timezone.utc).isoformat(),
            "totals": snapshot.get("summary", {}),
            "alerts": alerts[:10],
            "recommendations": recommendations[:8],
        }

    def weekly_summary(self, transactions: list[dict[str, Any]], insights: list[dict[str, Any]]) -> dict[str, Any]:
        spending = sum(abs(int(tx["amount_cents"])) for tx in transactions if int(tx["amount_cents"]) < 0)
        income = sum(int(tx["amount_cents"]) for tx in transactions if int(tx["amount_cents"]) > 0)
        return {
            "weekly_income_cents": income,
            "weekly_spend_cents": spending,
            "insight_count": len(insights),
            "insights": insights,
        }


def _alert(severity: str, title: str, message: str, reason: str, entity_type: str, entity_id: str, next_step: str) -> dict[str, Any]:
    return {
        "severity": severity,
        "title": title,
        "message": message,
        "reason": reason,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "suggested_next_step": next_step,
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "acked": False,
    }


def _day_of_month(ts: str) -> int:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).day
    except ValueError:
        return -1
