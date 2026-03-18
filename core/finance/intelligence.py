from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from statistics import mean
from typing import Any


# ===========================================================================
# Rule configuration
# ===========================================================================

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


# ===========================================================================
# E. ALERT ENGINE — deterministic, rule-based, explainable
# ===========================================================================

class FinanceAlertEngine:
    """Generates alerts from snapshot data using configurable rules.

    Every alert answers:
    - What data triggered this?
    - What rule produced it?
    - How severe is it?
    """

    def __init__(self, config: FinanceRuleConfig | None = None) -> None:
        self.config = config or DEFAULT_RULES

    def evaluate(self, snapshot: dict[str, Any], now: datetime | None = None) -> list[dict[str, Any]]:
        current = now or datetime.now(tz=timezone.utc)
        alerts: list[dict[str, Any]] = []
        alerts.extend(self._overspending_alerts(snapshot, current))
        alerts.extend(self._budget_alerts(snapshot, current))
        alerts.extend(self._bill_alerts(snapshot, current))
        alerts.extend(self._savings_alerts(snapshot, current))
        alerts.extend(self._credit_alerts(snapshot.get("cards", []), current))
        alerts.extend(self._unusual_spending_alerts(snapshot))
        return alerts

    def _overspending_alerts(self, snapshot: dict[str, Any], now: datetime) -> list[dict[str, Any]]:
        alerts: list[dict[str, Any]] = []
        transactions = snapshot.get("transactions", [])
        if not transactions:
            return alerts
        expenses = [abs(int(tx.get("amount_cents", 0))) for tx in transactions if _is_expense(tx)]
        if len(expenses) < 5:
            return alerts
        avg = mean(expenses)
        recent = expenses[:3]
        recent_avg = mean(recent) if recent else 0
        if recent_avg > avg * 1.5:
            alerts.append(_alert(
                alert_type="overspending",
                severity="caution",
                title="Recent spending above average",
                message=f"Recent transactions average {recent_avg / 100:.2f} vs overall average {avg / 100:.2f}.",
                source_rule="overspending_detection",
                entity_type="transactions",
                entity_id="recent",
                next_step="Review recent discretionary purchases and consider reducing spend.",
            ))
        return alerts

    def _budget_alerts(self, snapshot: dict[str, Any], now: datetime) -> list[dict[str, Any]]:
        alerts: list[dict[str, Any]] = []
        budgets = snapshot.get("budgets", [])
        transactions = snapshot.get("transactions", [])
        category_spend: dict[str, int] = defaultdict(int)
        total_spend = 0
        for tx in transactions:
            if _is_expense(tx):
                spent = abs(int(tx.get("amount_cents", 0)))
                cat = tx.get("category_id") or tx.get("category", "uncategorized")
                category_spend[cat] += spent
                total_spend += spent

        for budget in budgets:
            limit_cents = int(budget.get("amount_limit_cents", 0))
            if limit_cents <= 0:
                continue
            cat_id = budget.get("category_id")
            spent = category_spend.get(cat_id, 0) if cat_id else total_spend
            usage = spent / limit_cents
            if usage >= 1.0:
                alerts.append(_alert(
                    alert_type="budget_exceeded",
                    severity="urgent",
                    title="Budget exceeded",
                    message=f"Budget '{budget.get('name', '')}' at {usage:.0%} of limit.",
                    source_rule="budget_overspend",
                    entity_type="budget",
                    entity_id=budget.get("id", ""),
                    next_step="Reduce variable spend in this category immediately.",
                ))
            elif usage >= self.config.budget_category_warning_percent:
                alerts.append(_alert(
                    alert_type="budget_warning",
                    severity="caution",
                    title="Budget nearing limit",
                    message=f"Budget '{budget.get('name', '')}' at {usage:.0%} of limit.",
                    source_rule="budget_threshold_warning",
                    entity_type="budget",
                    entity_id=budget.get("id", ""),
                    next_step="Pace spending to avoid end-of-month overrun.",
                ))

        return alerts

    def _bill_alerts(self, snapshot: dict[str, Any], now: datetime) -> list[dict[str, Any]]:
        alerts: list[dict[str, Any]] = []
        bills = snapshot.get("bills", [])
        today = now.date()
        for bill in bills:
            status = bill.get("status", "pending")
            if status in ("paid", "cancelled"):
                continue
            due_str = bill.get("due_date", "")
            if not due_str:
                continue
            try:
                from datetime import date as date_type
                due = date_type.fromisoformat(due_str)
            except ValueError:
                continue
            days_until = (due - today).days
            if days_until < 0:
                alerts.append(_alert(
                    alert_type="bill_overdue",
                    severity="urgent",
                    title="Bill overdue",
                    message=f"'{bill.get('name', '')}' was due {abs(days_until)} day(s) ago.",
                    source_rule="bill_overdue_detection",
                    entity_type="bill",
                    entity_id=bill.get("id", ""),
                    next_step="Pay this bill immediately to avoid late fees.",
                ))
            elif days_until <= self.config.due_soon_days:
                alerts.append(_alert(
                    alert_type="bill_due_soon",
                    severity="caution",
                    title="Bill due soon",
                    message=f"'{bill.get('name', '')}' due in {days_until} day(s).",
                    source_rule="bill_due_soon_detection",
                    entity_type="bill",
                    entity_id=bill.get("id", ""),
                    next_step="Confirm payment is scheduled or pay now.",
                ))
        return alerts

    def _savings_alerts(self, snapshot: dict[str, Any], now: datetime) -> list[dict[str, Any]]:
        alerts: list[dict[str, Any]] = []
        goals = snapshot.get("savings_goals", [])
        for goal in goals:
            if goal.get("status") != "active":
                continue
            target = int(goal.get("target_amount_cents", 0))
            current = int(goal.get("current_progress_cents", 0))
            if target <= 0:
                continue
            progress = current / target
            target_date_str = goal.get("target_date")
            if target_date_str and progress < 1.0:
                try:
                    from datetime import date as date_type
                    target_date = date_type.fromisoformat(target_date_str)
                    days_left = (target_date - now.date()).days
                    if days_left <= 0:
                        alerts.append(_alert(
                            alert_type="savings_deadline_passed",
                            severity="caution",
                            title="Savings goal deadline passed",
                            message=f"Goal '{goal.get('name', '')}' deadline passed at {progress:.0%} progress.",
                            source_rule="savings_deadline_missed",
                            entity_type="savings_goal",
                            entity_id=goal.get("id", ""),
                            next_step="Re-evaluate target date or increase contribution pace.",
                        ))
                    elif days_left <= 30 and progress < 0.8:
                        alerts.append(_alert(
                            alert_type="savings_behind_pace",
                            severity="advisory",
                            title="Savings goal behind pace",
                            message=f"Goal '{goal.get('name', '')}' at {progress:.0%} with {days_left} days remaining.",
                            source_rule="savings_pace_warning",
                            entity_type="savings_goal",
                            entity_id=goal.get("id", ""),
                            next_step="Increase weekly contributions to catch up.",
                        ))
                except ValueError:
                    pass
        return alerts

    def _credit_alerts(self, cards: list[dict[str, Any]], now: datetime) -> list[dict[str, Any]]:
        alerts: list[dict[str, Any]] = []
        for card in cards:
            limit_cents = int(card.get("credit_limit_cents", 0))
            balance_cents = int(card.get("current_balance_cents", 0))
            if limit_cents <= 0:
                continue
            utilization = balance_cents / limit_cents
            if utilization >= self.config.credit_utilization_urgent:
                alerts.append(_alert(
                    alert_type="credit_utilization_high",
                    severity="urgent",
                    title="High card utilization",
                    message=f"{card.get('name', 'Card')} utilization is {utilization:.0%}.",
                    source_rule="credit_utilization_high",
                    entity_type="card",
                    entity_id=card.get("id", ""),
                    next_step="Pay down balance before statement closes.",
                ))
            elif utilization >= self.config.credit_utilization_caution:
                alerts.append(_alert(
                    alert_type="credit_utilization_elevated",
                    severity="caution",
                    title="Card utilization elevated",
                    message=f"{card.get('name', 'Card')} utilization is {utilization:.0%}.",
                    source_rule="credit_utilization_caution",
                    entity_type="card",
                    entity_id=card.get("id", ""),
                    next_step="Shift discretionary spend to debit or pay early.",
                ))
        return alerts

    def _unusual_spending_alerts(self, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
        alerts: list[dict[str, Any]] = []
        transactions = snapshot.get("transactions", [])
        if len(transactions) < 10:
            return alerts
        expenses = [(tx.get("merchant", ""), abs(int(tx.get("amount_cents", 0)))) for tx in transactions if _is_expense(tx)]
        if not expenses:
            return alerts
        amounts = [a for _, a in expenses]
        avg = mean(amounts)
        std_estimate = (max(amounts) - min(amounts)) / 4 if len(amounts) > 1 else avg
        threshold = avg + 2 * std_estimate
        for merchant, amount in expenses[:5]:
            if amount > threshold and amount > 5000:
                alerts.append(_alert(
                    alert_type="unusual_spending",
                    severity="advisory",
                    title="Unusual transaction amount",
                    message=f"Transaction of {amount / 100:.2f} at '{merchant or 'unknown'}' is significantly above average.",
                    source_rule="anomaly_detection_amount",
                    entity_type="transaction",
                    entity_id="",
                    next_step="Verify this was an intentional purchase.",
                ))
                break
        return alerts


# ===========================================================================
# F. INSIGHT ENGINE — data-backed, deterministic or marked heuristic
# ===========================================================================

class FinanceInsightEngine:
    """Generates insights from transaction data.

    Every insight is:
    - Data-backed with traceable source
    - Deterministic or clearly marked heuristic
    - Concise and explainable
    """

    def analyze(self, transactions: list[dict[str, Any]], date_from: str = "", date_to: str = "") -> list[dict[str, Any]]:
        insights: list[dict[str, Any]] = []
        if not transactions:
            return insights
        insights.extend(self._spending_by_category(transactions))
        insights.extend(self._merchant_breakdown(transactions))
        insights.extend(self._recurring_detection(transactions))
        insights.extend(self._month_over_month(transactions))
        insights.extend(self._top_spending_categories(transactions))
        insights.extend(self._spending_leaks(transactions))
        return insights

    def _spending_by_category(self, transactions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        category_totals: dict[str, int] = defaultdict(int)
        total = 0
        for tx in transactions:
            if _is_expense(tx):
                amount = abs(int(tx.get("amount_cents", 0)))
                cat = tx.get("category_id") or tx.get("category", "uncategorized")
                category_totals[cat] += amount
                total += amount
        if not category_totals or total == 0:
            return []
        top = sorted(category_totals.items(), key=lambda x: -x[1])[:3]
        top_desc = ", ".join(f"{cat} ({amt / 100:.2f})" for cat, amt in top)
        return [{
            "pattern": "category_breakdown",
            "score": round(top[0][1] / total, 2),
            "reason": f"Top spending categories: {top_desc}.",
            "suggestion": "Review top categories for reduction opportunities.",
            "data_source": "transaction_aggregation",
        }]

    def _merchant_breakdown(self, transactions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        merchant_totals: dict[str, int] = defaultdict(int)
        for tx in transactions:
            if _is_expense(tx):
                merchant = (tx.get("merchant") or "").strip().lower()
                if merchant:
                    merchant_totals[merchant] += abs(int(tx.get("amount_cents", 0)))
        if not merchant_totals:
            return []
        top = sorted(merchant_totals.items(), key=lambda x: -x[1])[:5]
        top_desc = ", ".join(f"{m} ({a / 100:.2f})" for m, a in top)
        return [{
            "pattern": "merchant_breakdown",
            "score": float(len(top)),
            "reason": f"Top merchants by spend: {top_desc}.",
            "suggestion": "Evaluate whether top merchants represent essential or discretionary spend.",
            "data_source": "transaction_aggregation",
        }]

    def _recurring_detection(self, transactions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        by_merchant: dict[str, list[int]] = defaultdict(list)
        for tx in transactions:
            if _is_expense(tx):
                merchant = (tx.get("merchant") or "").strip().lower()
                if merchant:
                    by_merchant[merchant].append(abs(int(tx.get("amount_cents", 0))))
        recurring = []
        for merchant, amounts in by_merchant.items():
            if len(amounts) >= 3:
                avg = int(mean(amounts))
                recurring.append({"merchant": merchant, "occurrences": len(amounts), "avg_cents": avg})
        if not recurring:
            return []
        recurring.sort(key=lambda x: -x["occurrences"])
        desc = ", ".join(f"{r['merchant']} ({r['occurrences']}x)" for r in recurring[:5])
        return [{
            "pattern": "recurring_expense_detection",
            "score": float(len(recurring)),
            "reason": f"Detected {len(recurring)} potential recurring expenses: {desc}.",
            "suggestion": "Review recurring charges for subscriptions that may no longer be needed.",
            "data_source": "merchant_frequency_analysis",
        }]

    def _month_over_month(self, transactions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        monthly: dict[str, int] = defaultdict(int)
        for tx in transactions:
            if _is_expense(tx):
                tx_date = tx.get("transaction_date", "")
                if len(tx_date) >= 7:
                    month_key = tx_date[:7]
                    monthly[month_key] += abs(int(tx.get("amount_cents", 0)))
        if len(monthly) < 2:
            return []
        sorted_months = sorted(monthly.items())
        latest = sorted_months[-1]
        previous = sorted_months[-2]
        if previous[1] == 0:
            return []
        change = (latest[1] - previous[1]) / previous[1]
        direction = "increased" if change > 0 else "decreased"
        return [{
            "pattern": "month_over_month_comparison",
            "score": round(abs(change), 2),
            "reason": f"Spending {direction} by {abs(change):.0%} from {previous[0]} to {latest[0]}.",
            "suggestion": f"{'Investigate the increase and identify contributing categories.' if change > 0.1 else 'Good trend — spending is stable or decreasing.'}",
            "data_source": "monthly_aggregation",
        }]

    def _top_spending_categories(self, transactions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        category_totals: dict[str, int] = defaultdict(int)
        for tx in transactions:
            if _is_expense(tx):
                cat = tx.get("category_id") or tx.get("category", "uncategorized")
                category_totals[cat] += abs(int(tx.get("amount_cents", 0)))
        if not category_totals:
            return []
        top = sorted(category_totals.items(), key=lambda x: -x[1])[:3]
        return [{
            "pattern": "top_spending_categories",
            "score": float(len(top)),
            "reason": f"Highest spending: {', '.join(f'{c} ({a / 100:.2f})' for c, a in top)}.",
            "suggestion": "Focus budget reduction efforts on the top category first.",
            "data_source": "category_ranking",
        }]

    def _spending_leaks(self, transactions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        small_txns: dict[str, int] = defaultdict(int)
        small_counts: dict[str, int] = defaultdict(int)
        for tx in transactions:
            if _is_expense(tx):
                amount = abs(int(tx.get("amount_cents", 0)))
                merchant = (tx.get("merchant") or "").strip().lower()
                if amount <= 1500 and merchant:
                    small_txns[merchant] += amount
                    small_counts[merchant] += 1
        leaks = [(m, small_txns[m], small_counts[m]) for m in small_txns if small_counts[m] >= 3]
        if not leaks:
            return []
        leaks.sort(key=lambda x: -x[1])
        desc = ", ".join(f"{m} ({c}x, total {t / 100:.2f})" for m, t, c in leaks[:3])
        total_leak = sum(t for _, t, _ in leaks)
        return [{
            "pattern": "spending_leaks",
            "score": round(total_leak / 100, 2),
            "reason": f"Small recurring charges adding up: {desc}. Total leak: {total_leak / 100:.2f}.",
            "suggestion": "Small frequent purchases add up — consider consolidating or eliminating.",
            "data_source": "small_transaction_pattern_analysis",
        }]


# ===========================================================================
# G. GUIDANCE ENGINE — bounded, explainable, never autonomous
# ===========================================================================

class FinanceGuidanceEngine:
    """Generates actionable guidance from current financial state.

    Guidance must not:
    - Automatically spend, transfer, trade, invest, or commit
    - Pretend certainty where only heuristics exist
    - Advice without traceable basis
    """

    def generate(
        self,
        transactions: list[dict[str, Any]],
        budgets: list[dict[str, Any]] | None = None,
        bills: list[dict[str, Any]] | None = None,
        savings_goals: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        guidance: list[dict[str, Any]] = []
        guidance.extend(self._overspending_guidance(transactions, budgets or []))
        guidance.extend(self._savings_guidance(savings_goals or []))
        guidance.extend(self._timing_guidance(bills or []))
        guidance.extend(self._subscription_guidance(transactions))
        guidance.extend(self._budget_adjustment_guidance(transactions, budgets or []))
        return guidance

    def _overspending_guidance(self, transactions: list[dict[str, Any]], budgets: list[dict[str, Any]]) -> list[dict[str, Any]]:
        guidance: list[dict[str, Any]] = []
        category_spend: dict[str, int] = defaultdict(int)
        for tx in transactions:
            if _is_expense(tx):
                cat = tx.get("category_id") or tx.get("category", "uncategorized")
                category_spend[cat] += abs(int(tx.get("amount_cents", 0)))

        for budget in budgets:
            limit = int(budget.get("amount_limit_cents", 0))
            cat_id = budget.get("category_id")
            if limit <= 0 or not cat_id:
                continue
            spent = category_spend.get(cat_id, 0)
            if spent > limit:
                overage = spent - limit
                guidance.append({
                    "title": f"Reduce spending in {cat_id}",
                    "message": f"Over budget by {overage / 100:.2f}. Consider deferring non-essential purchases in this category.",
                    "source": "budget_vs_actual_comparison",
                    "severity": "caution",
                    "traceable_basis": f"Budget limit: {limit / 100:.2f}, actual spend: {spent / 100:.2f}.",
                })
        return guidance

    def _savings_guidance(self, goals: list[dict[str, Any]]) -> list[dict[str, Any]]:
        guidance: list[dict[str, Any]] = []
        for goal in goals:
            if goal.get("status") != "active":
                continue
            target = int(goal.get("target_amount_cents", 0))
            current = int(goal.get("current_progress_cents", 0))
            if target <= 0:
                continue
            progress = current / target
            if progress < 0.25:
                guidance.append({
                    "title": f"Accelerate savings for '{goal.get('name', '')}'",
                    "message": f"Only {progress:.0%} toward goal. Consider setting up automatic transfers.",
                    "source": "savings_progress_analysis",
                    "severity": "advisory",
                    "traceable_basis": f"Target: {target / 100:.2f}, current: {current / 100:.2f}.",
                })
        return guidance

    def _timing_guidance(self, bills: list[dict[str, Any]]) -> list[dict[str, Any]]:
        guidance: list[dict[str, Any]] = []
        upcoming_total = 0
        for bill in bills:
            if bill.get("status") in ("paid", "cancelled"):
                continue
            amount = int(bill.get("amount_expected_cents", 0) or 0)
            upcoming_total += amount
        if upcoming_total > 0:
            guidance.append({
                "title": "Upcoming bill obligations",
                "message": f"You have {upcoming_total / 100:.2f} in upcoming bills. Ensure sufficient funds.",
                "source": "bill_due_date_scan",
                "severity": "info",
                "traceable_basis": f"Sum of pending bill amounts: {upcoming_total / 100:.2f}.",
            })
        return guidance

    def _subscription_guidance(self, transactions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        by_merchant: dict[str, int] = defaultdict(int)
        by_merchant_count: dict[str, int] = defaultdict(int)
        for tx in transactions:
            if _is_expense(tx):
                merchant = (tx.get("merchant") or "").strip().lower()
                if merchant:
                    by_merchant[merchant] += abs(int(tx.get("amount_cents", 0)))
                    by_merchant_count[merchant] += 1
        recurring = [(m, by_merchant[m]) for m in by_merchant if by_merchant_count[m] >= 3]
        if not recurring:
            return []
        recurring.sort(key=lambda x: -x[1])
        total = sum(a for _, a in recurring)
        return [{
            "title": "Review recurring subscriptions",
            "message": f"Detected {len(recurring)} recurring charges totaling {total / 100:.2f}. Review for unused subscriptions.",
            "source": "recurring_expense_pattern",
            "severity": "advisory",
            "traceable_basis": f"Merchants with 3+ transactions: {', '.join(m for m, _ in recurring[:5])}.",
        }]

    def _budget_adjustment_guidance(self, transactions: list[dict[str, Any]], budgets: list[dict[str, Any]]) -> list[dict[str, Any]]:
        guidance: list[dict[str, Any]] = []
        category_spend: dict[str, int] = defaultdict(int)
        for tx in transactions:
            if _is_expense(tx):
                cat = tx.get("category_id") or tx.get("category", "uncategorized")
                category_spend[cat] += abs(int(tx.get("amount_cents", 0)))
        for budget in budgets:
            limit = int(budget.get("amount_limit_cents", 0))
            cat_id = budget.get("category_id")
            if limit <= 0 or not cat_id:
                continue
            spent = category_spend.get(cat_id, 0)
            usage = spent / limit if limit > 0 else 0
            if usage < 0.3:
                guidance.append({
                    "title": f"Budget for {cat_id} may be too generous",
                    "message": f"Only {usage:.0%} used. Consider reallocating budget to areas with higher spend.",
                    "source": "budget_utilization_analysis",
                    "severity": "info",
                    "traceable_basis": f"Budget limit: {limit / 100:.2f}, actual spend: {spent / 100:.2f}.",
                })
        return guidance


# ===========================================================================
# Legacy FinanceCognition (backward compatibility)
# ===========================================================================

class FinanceCognition:
    """Lightweight, explainable pattern analysis for finance-only behavior."""

    def analyze(self, transactions: list[dict[str, Any]], paycheck_days: list[int] | None = None) -> list[dict[str, Any]]:
        insights: list[dict[str, Any]] = []
        if not transactions:
            return insights

        ordered = sorted(transactions, key=lambda item: str(item.get("ts", item.get("created_at", ""))), reverse=True)
        expenses = [abs(int(tx.get("amount_cents", 0))) for tx in ordered if _is_expense(tx)]
        if expenses:
            avg = mean(expenses)
            latest = expenses[0]
            if latest > avg * 1.6:
                insights.append({
                    "pattern": "spending_drift",
                    "score": round(latest / max(avg, 1), 2),
                    "reason": "Latest expense is significantly above baseline average.",
                    "suggestion": "Review recent discretionary purchases and rebalance this week.",
                })

        merchant_counts: dict[str, int] = defaultdict(int)
        for tx in transactions:
            merchant = (tx.get("merchant") or "").strip().lower()
            if merchant:
                merchant_counts[merchant] += 1
        frequent = [m for m, c in merchant_counts.items() if c >= 4]
        if frequent:
            insights.append({
                "pattern": "repeated_merchant_habit",
                "score": float(len(frequent)),
                "reason": f"Repeated spending found across {len(frequent)} merchants.",
                "suggestion": "Set merchant-level spending caps for top recurring discretionary merchants.",
            })

        if paycheck_days:
            payday_spend = 0
            non_payday_spend = 0
            for tx in transactions:
                if not _is_expense(tx):
                    continue
                day = _day_of_month(str(tx.get("ts", tx.get("created_at", ""))))
                amount = abs(int(tx.get("amount_cents", 0)))
                if day in paycheck_days:
                    payday_spend += amount
                else:
                    non_payday_spend += amount
            if payday_spend > non_payday_spend * 0.6 and payday_spend > 0:
                insights.append({
                    "pattern": "post_payday_spike",
                    "score": round(payday_spend / max(non_payday_spend, 1), 2),
                    "reason": "High share of spend occurs on known payday dates.",
                    "suggestion": "Use a 48-hour cooling rule for discretionary purchases after payday.",
                })
        return insights

    def detect_recurring_expenses(self, transactions: list[dict[str, Any]], min_occurrences: int = 3) -> list[dict[str, Any]]:
        by_merchant: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for tx in transactions:
            merchant = (tx.get("merchant") or "").strip().lower()
            if _is_expense(tx) and merchant:
                by_merchant[merchant].append(tx)

        recurring: list[dict[str, Any]] = []
        for merchant, txs in by_merchant.items():
            if len(txs) < min_occurrences:
                continue
            amounts = [abs(int(tx.get("amount_cents", 0))) for tx in txs]
            avg_amount = int(mean(amounts))
            recurring.append({
                "merchant": merchant,
                "occurrences": len(txs),
                "expected_amount_cents": avg_amount,
                "cadence_days": 30,
            })
        return sorted(recurring, key=lambda item: item["occurrences"], reverse=True)


# ===========================================================================
# Legacy compatibility aliases
# ===========================================================================

# Old code imports these names
FinanceRuleEngine = FinanceAlertEngine
FinanceRecommendationEngine = FinanceGuidanceEngine
FinanceReportingEngine = type("FinanceReportingEngine", (), {
    "daily_brief": lambda self, snapshot, alerts, recommendations: {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "totals": snapshot.get("summary", {}),
        "alerts": alerts[:10],
        "recommendations": recommendations[:8],
    },
    "weekly_summary": lambda self, transactions, insights: {
        "weekly_income_cents": sum(abs(int(tx.get("amount_cents", 0))) for tx in transactions if not _is_expense(tx)),
        "weekly_spend_cents": sum(abs(int(tx.get("amount_cents", 0))) for tx in transactions if _is_expense(tx)),
        "insight_count": len(insights),
        "insights": insights,
    },
})


# ===========================================================================
# Helpers
# ===========================================================================

def _is_expense(tx: dict[str, Any]) -> bool:
    direction = tx.get("direction", "")
    if direction == "expense":
        return True
    if direction == "income":
        return False
    return int(tx.get("amount_cents", 0)) < 0


def _alert(
    alert_type: str,
    severity: str,
    title: str,
    message: str,
    source_rule: str,
    entity_type: str,
    entity_id: str,
    next_step: str,
) -> dict[str, Any]:
    return {
        "type": alert_type,
        "severity": severity,
        "title": title,
        "message": message,
        "source_rule": source_rule,
        "reason": source_rule,
        "related_entity_type": entity_type,
        "related_entity_id": entity_id,
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
