from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from core.finance.audit import finance_audit
from core.finance.intelligence import (
    DEFAULT_RULES,
    FinanceAlertEngine,
    FinanceCognition,
    FinanceGuidanceEngine,
    FinanceInsightEngine,
    FinanceRuleConfig,
)
from core.finance.policy import (
    FinanceNotFoundError,
    FinanceValidationError,
    enforce_policy,
    is_sensitive_action,
)
from core.finance.repository import FinanceRepository
from core.finance.schemas import (
    AccountCreate,
    AccountRecord,
    AccountResponse,
    AccountSummary,
    AccountUpdate,
    AccountsResponse,
    AlertRecord,
    AlertsResponse,
    BillCreate,
    BillRecord,
    BillResponse,
    BillsResponse,
    BillUpdate,
    BudgetCreate,
    BudgetRecord,
    BudgetResponse,
    BudgetStatusRecord,
    BudgetStatusResponse,
    BudgetsResponse,
    BudgetUpdate,
    CategoryCreate,
    CategoryRecord,
    CategorySummary,
    CategoryUpdate,
    CategoriesResponse,
    DeleteResult,
    GuidanceRecord,
    GuidanceResponse,
    InsightRecord,
    InsightsResponse,
    LegacySummaryReport,
    SavingsGoalCreate,
    SavingsGoalRecord,
    SavingsGoalResponse,
    SavingsGoalsResponse,
    SavingsGoalUpdate,
    SavingsProgressUpdate,
    SavingsStatusRecord,
    SavingsStatusResponse,
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


def _utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _to_transaction_record(item: Any) -> TransactionRecord:
    return TransactionRecord(**item.__dict__)


def _to_account_record(item: Any) -> AccountRecord:
    return AccountRecord(**item.__dict__)


def _to_budget_record(item: Any) -> BudgetRecord:
    return BudgetRecord(**item.__dict__)


def _to_bill_record(item: Any) -> BillRecord:
    return BillRecord(**item.__dict__)


def _to_savings_record(item: Any) -> SavingsGoalRecord:
    return SavingsGoalRecord(**item.__dict__)


def _to_alert_record(item: Any) -> AlertRecord:
    return AlertRecord(**item.__dict__)


def _to_category_record(item: Any) -> CategoryRecord:
    return CategoryRecord(**item.__dict__)


# ===========================================================================
# Finance Service — all 7 functional blocks
# ===========================================================================

class FinanceService:
    def __init__(self, repository: FinanceRepository | None = None) -> None:
        self.repository = repository or FinanceRepository()

    # -----------------------------------------------------------------------
    # A. LEDGER CORE — Accounts
    # -----------------------------------------------------------------------

    def create_account(self, payload: AccountCreate) -> AccountResponse:
        enforce_policy("create_account")
        account = self.repository.create_account(
            account_id=None,
            name=payload.name,
            account_type=payload.account_type,
            currency=payload.currency,
            institution=payload.institution,
            is_active=payload.is_active,
        )
        finance_audit("finance_account_created", account_id=account.id, account_type=account.account_type)
        return AccountResponse(account=_to_account_record(account))

    def update_account(self, account_id: str, payload: AccountUpdate) -> AccountResponse:
        enforce_policy("update_account")
        existing = self.repository.get_account(account_id)
        if existing is None:
            raise FinanceNotFoundError(f"Account '{account_id}' not found")
        updates: dict[str, Any] = {}
        if payload.name is not None:
            updates["name"] = payload.name
        if payload.account_type is not None:
            updates["account_type"] = payload.account_type
        if payload.currency is not None:
            updates["currency"] = payload.currency
        if "institution" in payload.model_fields_set:
            updates["institution"] = payload.institution
        if payload.is_active is not None:
            updates["is_active"] = 1 if payload.is_active else 0
        account = self.repository.update_account(account_id, updates)
        if account is None:
            raise FinanceNotFoundError(f"Account '{account_id}' not found")
        finance_audit("finance_account_updated", account_id=account_id, changed_fields=sorted(updates.keys()))
        return AccountResponse(account=_to_account_record(account))

    def get_account(self, account_id: str) -> AccountResponse:
        enforce_policy("get_account")
        account = self.repository.get_account(account_id)
        if account is None:
            raise FinanceNotFoundError(f"Account '{account_id}' not found")
        return AccountResponse(account=_to_account_record(account))

    def list_accounts(self) -> AccountsResponse:
        enforce_policy("list_accounts")
        accounts = self.repository.list_accounts()
        records = [_to_account_record(a) for a in accounts]
        return AccountsResponse(results=records, count=len(records))

    # -----------------------------------------------------------------------
    # A. LEDGER CORE — Categories
    # -----------------------------------------------------------------------

    def create_category(self, payload: CategoryCreate) -> CategoryRecord:
        enforce_policy("create_category")
        category = self.repository.create_category(
            category_id=None,
            name=payload.name,
            cat_type=payload.type,
            parent_category=payload.parent_category,
            is_system=False,
        )
        finance_audit("finance_category_created", category_id=category.id, name=category.name)
        return _to_category_record(category)

    def update_category(self, category_id: str, payload: CategoryUpdate) -> CategoryRecord:
        enforce_policy("update_category")
        existing = self.repository.get_category(category_id)
        if existing is None:
            raise FinanceNotFoundError(f"Category '{category_id}' not found")
        updates: dict[str, Any] = {}
        if payload.name is not None:
            updates["name"] = payload.name
        if payload.type is not None:
            updates["type"] = payload.type
        if "parent_category" in payload.model_fields_set:
            updates["parent_category"] = payload.parent_category
        category = self.repository.update_category(category_id, updates)
        if category is None:
            raise FinanceNotFoundError(f"Category '{category_id}' not found")
        finance_audit("finance_category_updated", category_id=category_id, changed_fields=sorted(updates.keys()))
        return _to_category_record(category)

    def list_categories(self) -> CategoriesResponse:
        enforce_policy("list_categories")
        categories = self.repository.list_categories()
        records = [_to_category_record(c) for c in categories]
        return CategoriesResponse(results=records, count=len(records))

    # -----------------------------------------------------------------------
    # A. LEDGER CORE — Transactions
    # -----------------------------------------------------------------------

    def add_transaction(self, payload: TransactionWrite) -> TransactionResponse:
        enforce_policy("add_transaction")
        if payload.account_id and self.repository.get_account(payload.account_id) is None:
            raise FinanceValidationError(f"Unknown account_id '{payload.account_id}'")
        category = self.repository.ensure_category(payload.category or "uncategorized")
        now = _utc_now_iso()
        record = {
            "id": str(uuid4()),
            "ts": now,
            "amount_cents": payload.amount_cents,
            "currency": payload.currency,
            "merchant": payload.merchant,
            "transaction_date": payload.transaction_date.isoformat(),
            "category_id": category.id,
            "account_id": payload.account_id,
            "direction": payload.direction,
            "payment_method": payload.payment_method,
            "notes": payload.notes,
            "source": payload.source,
            "tags": payload.tags,
            "created_at": now,
            "updated_at": now,
        }
        transaction = self.repository.create_transaction(record)
        finance_audit(
            "finance_transaction_created",
            transaction_id=transaction.id,
            amount_cents=transaction.amount_cents,
            currency=transaction.currency,
            category_id=transaction.category_id,
            direction=transaction.direction,
            merchant=transaction.merchant,
            notes=transaction.notes,
        )
        return TransactionResponse(transaction=_to_transaction_record(transaction))

    def get_transaction(self, transaction_id: str) -> TransactionResponse:
        enforce_policy("get_transaction")
        transaction = self.repository.get_transaction(transaction_id)
        if transaction is None:
            raise FinanceNotFoundError(f"Transaction '{transaction_id}' not found")
        finance_audit("finance_transaction_read", transaction_id=transaction_id)
        return TransactionResponse(transaction=_to_transaction_record(transaction))

    def update_transaction(self, transaction_id: str, payload: TransactionUpdate) -> TransactionResponse:
        enforce_policy("update_transaction")
        existing = self.repository.get_transaction(transaction_id)
        if existing is None:
            raise FinanceNotFoundError(f"Transaction '{transaction_id}' not found")
        if payload.account_id and self.repository.get_account(payload.account_id) is None:
            raise FinanceValidationError(f"Unknown account_id '{payload.account_id}'")
        updates: dict[str, Any] = {}
        if payload.amount is not None:
            updates["amount_cents"] = payload.amount_cents
        if payload.currency is not None:
            updates["currency"] = payload.currency
        if payload.category is not None:
            category = self.repository.ensure_category(payload.category)
            updates["category_id"] = category.id
        if "merchant" in payload.model_fields_set:
            updates["merchant"] = payload.merchant
        if "notes" in payload.model_fields_set:
            updates["notes"] = payload.notes
        if "account_id" in payload.model_fields_set:
            updates["account_id"] = payload.account_id
        if payload.direction is not None:
            updates["direction"] = payload.direction
        if "payment_method" in payload.model_fields_set:
            updates["payment_method"] = payload.payment_method
        if payload.transaction_date is not None:
            updates["transaction_date"] = payload.transaction_date.isoformat()
        if "tags" in payload.model_fields_set:
            updates["tags"] = payload.tags
        transaction = self.repository.update_transaction(transaction_id, updates)
        if transaction is None:
            raise FinanceNotFoundError(f"Transaction '{transaction_id}' not found")
        finance_audit(
            "finance_transaction_updated",
            transaction_id=transaction_id,
            changed_fields=sorted(updates.keys()),
            notes=payload.notes if "notes" in payload.model_fields_set else None,
        )
        return TransactionResponse(transaction=_to_transaction_record(transaction))

    def delete_transaction(self, transaction_id: str) -> DeleteResult:
        enforce_policy("delete_transaction")
        deleted = self.repository.delete_transaction(transaction_id)
        finance_audit("finance_transaction_deleted", transaction_id=transaction_id, deleted=deleted)
        if not deleted:
            raise FinanceNotFoundError(f"Transaction '{transaction_id}' not found")
        return DeleteResult(deleted=True, id=transaction_id)

    def list_transactions(self, filters: TransactionListFilters) -> TransactionsResponse:
        enforce_policy("list_transactions")
        results = self.repository.list_transactions(
            date_from=filters.date_from.isoformat() if isinstance(filters.date_from, date) else None,
            date_to=filters.date_to.isoformat() if isinstance(filters.date_to, date) else None,
            category=filters.category,
            account_id=filters.account_id,
            direction=filters.direction,
            merchant=filters.merchant,
            limit=filters.limit,
        )
        finance_audit(
            "finance_transactions_listed",
            result_count=len(results),
        )
        return TransactionsResponse(results=[_to_transaction_record(item) for item in results], count=len(results))

    # -----------------------------------------------------------------------
    # A. LEDGER CORE — Summaries
    # -----------------------------------------------------------------------

    def get_spending_summary(self, request: SpendingSummaryRequest) -> SpendingSummary:
        enforce_policy("get_spending_summary")
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
            by_merchant=snapshot["by_merchant"],
            by_direction=snapshot["by_direction"],
        )
        finance_audit(
            "finance_spending_summary_generated",
            date_from=response.date_from,
            date_to=response.date_to,
            expense_cents=response.totals.expense_cents,
        )
        return response

    def get_category_summary(self, request: SpendingSummaryRequest) -> CategorySummary:
        enforce_policy("get_category_summary")
        spending = self.get_spending_summary(request)
        categories = [
            {"category": category, "expense_cents": amount}
            for category, amount in sorted(spending.by_category.items(), key=lambda item: (-item[1], item[0]))
        ]
        finance_audit("finance_category_summary_generated", category_count=len(categories))
        return CategorySummary(
            date_from=spending.date_from,
            date_to=spending.date_to,
            account_id=spending.account_id,
            categories=categories,
        )

    def get_account_summary(self, request: SpendingSummaryRequest) -> AccountSummary:
        enforce_policy("get_account_summary")
        spending = self.get_spending_summary(request)
        accounts = [
            {"account": account, "total_cents": amount}
            for account, amount in sorted(spending.by_account.items(), key=lambda item: (-item[1], item[0]))
        ]
        finance_audit("finance_account_summary_generated", account_count=len(accounts))
        return AccountSummary(
            date_from=spending.date_from,
            date_to=spending.date_to,
            accounts=accounts,
        )

    # -----------------------------------------------------------------------
    # B. BUDGETING
    # -----------------------------------------------------------------------

    def create_budget(self, payload: BudgetCreate) -> BudgetResponse:
        enforce_policy("create_budget")
        now = _utc_now_iso()
        record = {
            "id": str(uuid4()),
            "name": payload.name,
            "category_id": payload.category_id,
            "account_id": payload.account_id,
            "amount_limit_cents": payload.amount_limit_cents,
            "currency": payload.currency,
            "period": payload.period,
            "warning_threshold_percent": payload.warning_threshold_percent,
            "created_at": now,
            "updated_at": now,
        }
        budget = self.repository.create_budget(record)
        finance_audit("finance_budget_created", budget_id=budget.id, name=budget.name)
        return BudgetResponse(budget=_to_budget_record(budget))

    def update_budget(self, budget_id: str, payload: BudgetUpdate) -> BudgetResponse:
        enforce_policy("update_budget")
        existing = self.repository.get_budget(budget_id)
        if existing is None:
            raise FinanceNotFoundError(f"Budget '{budget_id}' not found")
        updates: dict[str, Any] = {}
        if payload.name is not None:
            updates["name"] = payload.name
        if "category_id" in payload.model_fields_set:
            updates["category_id"] = payload.category_id
        if "account_id" in payload.model_fields_set:
            updates["account_id"] = payload.account_id
        if payload.amount_limit is not None:
            updates["amount_limit_cents"] = payload.amount_limit_cents
        if payload.currency is not None:
            updates["currency"] = payload.currency
        if payload.period is not None:
            updates["period"] = payload.period
        if payload.warning_threshold_percent is not None:
            updates["warning_threshold_percent"] = payload.warning_threshold_percent
        if payload.is_active is not None:
            updates["is_active"] = 1 if payload.is_active else 0
        budget = self.repository.update_budget(budget_id, updates)
        if budget is None:
            raise FinanceNotFoundError(f"Budget '{budget_id}' not found")
        finance_audit("finance_budget_updated", budget_id=budget_id, changed_fields=sorted(updates.keys()))
        return BudgetResponse(budget=_to_budget_record(budget))

    def delete_budget(self, budget_id: str) -> DeleteResult:
        enforce_policy("delete_budget")
        deleted = self.repository.delete_budget(budget_id)
        finance_audit("finance_budget_deleted", budget_id=budget_id, deleted=deleted)
        if not deleted:
            raise FinanceNotFoundError(f"Budget '{budget_id}' not found")
        return DeleteResult(deleted=True, id=budget_id)

    def list_budgets(self) -> BudgetsResponse:
        enforce_policy("list_budgets")
        budgets = self.repository.list_budgets()
        records = [_to_budget_record(b) for b in budgets]
        return BudgetsResponse(results=records, count=len(records))

    def get_budget_status(self) -> BudgetStatusResponse:
        enforce_policy("get_budget_status")
        budgets = self.repository.list_budgets()
        now = datetime.now(tz=timezone.utc)
        first_of_month = now.replace(day=1).date().isoformat()
        today = now.date().isoformat()
        snapshot = self.repository.summarize_spending(date_from=first_of_month, date_to=today, account_id=None)
        by_category = snapshot.get("by_category", {})
        total_spent = snapshot.get("expense_cents", 0)
        statuses: list[BudgetStatusRecord] = []
        for budget in budgets:
            if budget.category_id:
                spent = by_category.get(budget.category_id, 0)
            else:
                spent = total_spent
            remaining = budget.amount_limit_cents - spent
            usage_pct = (spent / budget.amount_limit_cents * 100) if budget.amount_limit_cents > 0 else 0.0
            if usage_pct >= 100:
                status_label = "exceeded"
            elif usage_pct >= budget.warning_threshold_percent:
                status_label = "warning"
            else:
                status_label = "under"
            statuses.append(BudgetStatusRecord(
                budget=_to_budget_record(budget),
                spent_cents=spent,
                remaining_cents=max(remaining, 0),
                usage_percent=round(usage_pct, 1),
                status=status_label,
            ))
        finance_audit("finance_budget_status_evaluated", budget_count=len(statuses))
        return BudgetStatusResponse(results=statuses, count=len(statuses))

    # -----------------------------------------------------------------------
    # C. BILLS / OBLIGATIONS / REMINDERS
    # -----------------------------------------------------------------------

    def create_bill(self, payload: BillCreate) -> BillResponse:
        enforce_policy("create_bill")
        now = _utc_now_iso()
        record = {
            "id": str(uuid4()),
            "name": payload.name,
            "amount_expected_cents": payload.amount_expected_cents,
            "currency": payload.currency,
            "due_date": payload.due_date.isoformat(),
            "recurrence_rule": payload.recurrence_rule,
            "category_id": payload.category_id,
            "account_id": payload.account_id,
            "auto_reminder": payload.auto_reminder,
            "notes": payload.notes,
            "created_at": now,
            "updated_at": now,
        }
        bill = self.repository.create_bill(record)
        finance_audit("finance_bill_created", bill_id=bill.id, name=bill.name)
        return BillResponse(bill=_to_bill_record(bill))

    def update_bill(self, bill_id: str, payload: BillUpdate) -> BillResponse:
        enforce_policy("update_bill")
        existing = self.repository.get_bill(bill_id)
        if existing is None:
            raise FinanceNotFoundError(f"Bill '{bill_id}' not found")
        updates: dict[str, Any] = {}
        if payload.name is not None:
            updates["name"] = payload.name
        if payload.amount_expected is not None:
            updates["amount_expected_cents"] = payload.amount_expected_cents
        if payload.currency is not None:
            updates["currency"] = payload.currency
        if payload.due_date is not None:
            updates["due_date"] = payload.due_date.isoformat()
        if "recurrence_rule" in payload.model_fields_set:
            updates["recurrence_rule"] = payload.recurrence_rule
        if "category_id" in payload.model_fields_set:
            updates["category_id"] = payload.category_id
        if "account_id" in payload.model_fields_set:
            updates["account_id"] = payload.account_id
        if payload.auto_reminder is not None:
            updates["auto_reminder"] = 1 if payload.auto_reminder else 0
        if "notes" in payload.model_fields_set:
            updates["notes"] = payload.notes
        if payload.status is not None:
            updates["status"] = payload.status
        bill = self.repository.update_bill(bill_id, updates)
        if bill is None:
            raise FinanceNotFoundError(f"Bill '{bill_id}' not found")
        finance_audit("finance_bill_updated", bill_id=bill_id, changed_fields=sorted(updates.keys()))
        return BillResponse(bill=_to_bill_record(bill))

    def delete_bill(self, bill_id: str) -> DeleteResult:
        enforce_policy("delete_bill")
        deleted = self.repository.delete_bill(bill_id)
        finance_audit("finance_bill_deleted", bill_id=bill_id, deleted=deleted)
        if not deleted:
            raise FinanceNotFoundError(f"Bill '{bill_id}' not found")
        return DeleteResult(deleted=True, id=bill_id)

    def mark_bill_paid(self, bill_id: str) -> BillResponse:
        enforce_policy("mark_bill_paid")
        existing = self.repository.get_bill(bill_id)
        if existing is None:
            raise FinanceNotFoundError(f"Bill '{bill_id}' not found")
        if existing.status == "paid":
            raise FinanceValidationError(f"Bill '{bill_id}' is already marked as paid")
        if existing.status == "cancelled":
            raise FinanceValidationError(f"Bill '{bill_id}' is cancelled and cannot be marked as paid")
        bill = self.repository.update_bill(bill_id, {"status": "paid"})
        if bill is None:
            raise FinanceNotFoundError(f"Bill '{bill_id}' not found")
        finance_audit("finance_bill_marked_paid", bill_id=bill_id)
        return BillResponse(bill=_to_bill_record(bill))

    def list_bills(self) -> BillsResponse:
        enforce_policy("list_bills")
        bills = self.repository.list_bills()
        records = [_to_bill_record(b) for b in bills]
        return BillsResponse(results=records, count=len(records))

    def get_due_bills(self) -> BillsResponse:
        enforce_policy("get_due_bills")
        today = datetime.now(tz=timezone.utc).date()
        upcoming = today + timedelta(days=7)
        bills = self.repository.get_due_bills(before_date=upcoming.isoformat())
        records = [_to_bill_record(b) for b in bills]
        finance_audit("finance_due_bills_checked", count=len(records))
        return BillsResponse(results=records, count=len(records))

    # -----------------------------------------------------------------------
    # D. SAVINGS GOALS
    # -----------------------------------------------------------------------

    def create_savings_goal(self, payload: SavingsGoalCreate) -> SavingsGoalResponse:
        enforce_policy("create_savings_goal")
        now = _utc_now_iso()
        record = {
            "id": str(uuid4()),
            "name": payload.name,
            "target_amount_cents": payload.target_amount_cents,
            "currency": payload.currency,
            "target_date": payload.target_date.isoformat() if payload.target_date else None,
            "linked_account_id": payload.linked_account_id,
            "created_at": now,
            "updated_at": now,
        }
        goal = self.repository.create_savings_goal(record)
        finance_audit("finance_savings_goal_created", goal_id=goal.id, name=goal.name)
        return SavingsGoalResponse(goal=_to_savings_record(goal))

    def update_savings_goal(self, goal_id: str, payload: SavingsGoalUpdate) -> SavingsGoalResponse:
        enforce_policy("update_savings_goal")
        existing = self.repository.get_savings_goal(goal_id)
        if existing is None:
            raise FinanceNotFoundError(f"Savings goal '{goal_id}' not found")
        updates: dict[str, Any] = {}
        if payload.name is not None:
            updates["name"] = payload.name
        if payload.target_amount is not None:
            updates["target_amount_cents"] = payload.target_amount_cents
        if payload.currency is not None:
            updates["currency"] = payload.currency
        if "target_date" in payload.model_fields_set:
            updates["target_date"] = payload.target_date.isoformat() if payload.target_date else None
        if "linked_account_id" in payload.model_fields_set:
            updates["linked_account_id"] = payload.linked_account_id
        if payload.status is not None:
            updates["status"] = payload.status
        goal = self.repository.update_savings_goal(goal_id, updates)
        if goal is None:
            raise FinanceNotFoundError(f"Savings goal '{goal_id}' not found")
        finance_audit("finance_savings_goal_updated", goal_id=goal_id, changed_fields=sorted(updates.keys()))
        return SavingsGoalResponse(goal=_to_savings_record(goal))

    def record_savings_progress(self, goal_id: str, payload: SavingsProgressUpdate) -> SavingsGoalResponse:
        enforce_policy("record_savings_progress")
        existing = self.repository.get_savings_goal(goal_id)
        if existing is None:
            raise FinanceNotFoundError(f"Savings goal '{goal_id}' not found")
        if existing.status != "active":
            raise FinanceValidationError(f"Savings goal '{goal_id}' is not active")
        goal = self.repository.record_savings_progress(goal_id, payload.amount_cents)
        if goal is None:
            raise FinanceNotFoundError(f"Savings goal '{goal_id}' not found")
        finance_audit("finance_savings_progress_recorded", goal_id=goal_id, amount_cents=payload.amount_cents)
        return SavingsGoalResponse(goal=_to_savings_record(goal))

    def list_savings_goals(self) -> SavingsGoalsResponse:
        enforce_policy("list_savings_goals")
        goals = self.repository.list_savings_goals()
        records = [_to_savings_record(g) for g in goals]
        return SavingsGoalsResponse(results=records, count=len(records))

    def get_savings_status(self) -> SavingsStatusResponse:
        enforce_policy("get_savings_status")
        goals = self.repository.list_savings_goals()
        statuses: list[SavingsStatusRecord] = []
        today = datetime.now(tz=timezone.utc).date()
        for goal in goals:
            remaining = goal.target_amount_cents - goal.current_progress_cents
            progress_pct = (goal.current_progress_cents / goal.target_amount_cents * 100) if goal.target_amount_cents > 0 else 0.0
            on_track = True
            if goal.target_date:
                try:
                    target = date.fromisoformat(goal.target_date)
                    days_left = (target - today).days
                    if days_left > 0 and remaining > 0:
                        daily_needed = remaining / days_left
                        monthly_needed = daily_needed * 30
                        on_track = monthly_needed <= goal.target_amount_cents * 0.15
                    elif days_left <= 0 and remaining > 0:
                        on_track = False
                except ValueError:
                    pass
            statuses.append(SavingsStatusRecord(
                goal=_to_savings_record(goal),
                remaining_cents=max(remaining, 0),
                progress_percent=round(progress_pct, 1),
                on_track=on_track,
            ))
        finance_audit("finance_savings_status_evaluated", goal_count=len(statuses))
        return SavingsStatusResponse(results=statuses, count=len(statuses))

    # -----------------------------------------------------------------------
    # E. ALERTS
    # -----------------------------------------------------------------------

    def list_alerts(self, limit: int = 100) -> AlertsResponse:
        enforce_policy("list_alerts")
        alerts = self.repository.list_alerts(limit=limit)
        records = [_to_alert_record(a) for a in alerts]
        return AlertsResponse(results=records, count=len(records))

    def resolve_alert(self, alert_id: str) -> AlertRecord:
        enforce_policy("resolve_alert")
        alert = self.repository.resolve_alert(alert_id)
        if alert is None:
            raise FinanceNotFoundError(f"Alert '{alert_id}' not found")
        finance_audit("finance_alert_resolved", alert_id=alert_id)
        return _to_alert_record(alert)

    # -----------------------------------------------------------------------
    # F. INSIGHTS
    # -----------------------------------------------------------------------

    def get_insights(self, date_from: str, date_to: str) -> InsightsResponse:
        enforce_policy("get_insights")
        transactions = self.repository.list_transactions(
            date_from=date_from, date_to=date_to, limit=500,
        )
        tx_dicts = [tx.__dict__ for tx in transactions]
        engine = FinanceInsightEngine()
        insights = engine.analyze(tx_dicts, date_from=date_from, date_to=date_to)
        records = [InsightRecord(**i) for i in insights]
        finance_audit("finance_insights_generated", count=len(records))
        return InsightsResponse(results=records, date_from=date_from, date_to=date_to)

    # -----------------------------------------------------------------------
    # G. GUIDANCE
    # -----------------------------------------------------------------------

    def get_guidance(self) -> GuidanceResponse:
        enforce_policy("get_guidance")
        now = datetime.now(tz=timezone.utc)
        first_of_month = now.replace(day=1).date().isoformat()
        today = now.date().isoformat()
        transactions = self.repository.list_transactions(
            date_from=first_of_month, date_to=today, limit=500,
        )
        budgets = self.repository.list_budgets()
        bills = self.repository.get_due_bills(before_date=(now.date() + timedelta(days=14)).isoformat())
        goals = self.repository.list_savings_goals()
        tx_dicts = [tx.__dict__ for tx in transactions]
        engine = FinanceGuidanceEngine()
        guidance = engine.generate(
            transactions=tx_dicts,
            budgets=[b.__dict__ for b in budgets],
            bills=[b.__dict__ for b in bills],
            savings_goals=[g.__dict__ for g in goals],
        )
        records = [GuidanceRecord(**g) for g in guidance]
        finance_audit("finance_guidance_generated", count=len(records))
        return GuidanceResponse(results=records, count=len(records))

    # -----------------------------------------------------------------------
    # Intelligence brief (composite)
    # -----------------------------------------------------------------------

    def generate_brief(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        enforce_policy("generate_brief")
        transactions = snapshot.get("transactions") or []
        cognition = FinanceCognition()
        insights = cognition.analyze(transactions, paycheck_days=snapshot.get("paycheck_days"))
        recurring = cognition.detect_recurring_expenses(transactions)

        config = self._load_rule_config()
        alert_engine = FinanceAlertEngine(config=config)
        alerts = alert_engine.evaluate(snapshot)

        guidance_engine = FinanceGuidanceEngine()
        guidance = guidance_engine.generate(
            transactions=transactions,
            budgets=snapshot.get("budgets", []),
            bills=snapshot.get("bills", []),
            savings_goals=snapshot.get("savings_goals", []),
        )

        for alert in alerts:
            self.repository.create_alert({
                "id": str(uuid4()),
                "type": alert.get("type", "rule_based"),
                "severity": alert["severity"],
                "title": alert["title"],
                "message": alert["message"],
                "source_rule": alert.get("source_rule", alert.get("reason", "")),
                "related_entity_type": alert.get("related_entity_type", alert.get("entity_type")),
                "related_entity_id": alert.get("related_entity_id", alert.get("entity_id")),
                "created_at": alert.get("timestamp", _utc_now_iso()),
            })
        for insight in insights:
            self.repository.add_behavior_log({
                "id": str(uuid4()),
                "behavior_type": insight["pattern"],
                "score": float(insight["score"]),
                "details": insight,
                "ts": _utc_now_iso(),
            })

        finance_audit(
            "finance_intelligence_brief_generated",
            alert_count=len(alerts),
            guidance_count=len(guidance),
            recurring_count=len(recurring),
            insight_count=len(insights),
        )
        return {
            "alerts": alerts,
            "guidance": guidance,
            "recurring_expenses": recurring,
            "behavior_insights": insights,
        }

    # -----------------------------------------------------------------------
    # Rules
    # -----------------------------------------------------------------------

    def set_rule_threshold(self, rule_key: str, threshold_value: float, enabled: bool = True) -> dict[str, Any]:
        enforce_policy("set_rule_threshold")
        if rule_key not in DEFAULT_RULE_THRESHOLDS:
            raise FinanceValidationError(f"Unsupported rule '{rule_key}'")
        self.repository.upsert_rule(rule_key, threshold_value, enabled)
        finance_audit("finance_rule_threshold_set", rule_key=rule_key, threshold_value=threshold_value, enabled=enabled)
        return {"rule_key": rule_key, "threshold_value": threshold_value, "enabled": enabled, "updated_at": _utc_now_iso()}

    def get_rule_thresholds(self) -> dict[str, dict[str, Any]]:
        enforce_policy("get_rule_thresholds")
        configured = self.repository.list_rules()
        output: dict[str, dict[str, Any]] = {}
        for key, default in DEFAULT_RULE_THRESHOLDS.items():
            if key in configured:
                output[key] = configured[key]
            else:
                output[key] = {"threshold_value": default, "enabled": True}
        return output

    def _load_rule_config(self) -> FinanceRuleConfig:
        configured = self.repository.list_rules()
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

    # -----------------------------------------------------------------------
    # Behavior logs
    # -----------------------------------------------------------------------

    def list_behavior_logs(self, limit: int = 100) -> list[dict[str, Any]]:
        return self.repository.list_behavior_logs(limit=limit)


# ===========================================================================
# Module-level singleton
# ===========================================================================

_FINANCE_SERVICE = FinanceService()


# ===========================================================================
# Backward-compatible function API
# ===========================================================================

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
    direction = "expense" if amount_cents < 0 else "income"
    response = _FINANCE_SERVICE.add_transaction(
        TransactionWrite(
            amount=abs(amount_cents) / 100,
            currency=currency,
            category=category,
            merchant=merchant,
            notes=note,
            payment_method=method,
            source=source,
            account_id=account_id,
            transaction_date=transaction_date,
            direction=direction,
        )
    )
    return response.transaction.id


def get_transaction(transaction_id: str) -> dict[str, Any]:
    return _FINANCE_SERVICE.get_transaction(transaction_id).model_dump()["transaction"]


def update_transaction(transaction_id: str, **updates: Any) -> dict[str, Any]:
    # Map old field names to new
    if "note" in updates:
        updates["notes"] = updates.pop("note")
    if "method" in updates:
        updates["payment_method"] = updates.pop("method")
    payload = TransactionUpdate(**updates)
    return _FINANCE_SERVICE.update_transaction(transaction_id, payload).model_dump()["transaction"]


def delete_transaction(transaction_id: str) -> dict[str, Any]:
    result = _FINANCE_SERVICE.delete_transaction(transaction_id)
    return {"deleted": result.deleted, "transaction_id": result.id}


def upsert_account(**kwargs: Any) -> dict[str, Any]:
    response = _FINANCE_SERVICE.create_account(AccountCreate(**kwargs))
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
    return _FINANCE_SERVICE.list_transactions(filters).model_dump()["results"]


def spending_summary(date_from: str, date_to: str, account_id: str | None = None) -> dict[str, Any]:
    request = SpendingSummaryRequest(date_from=date_from, date_to=date_to, account_id=account_id)
    return _FINANCE_SERVICE.get_spending_summary(request).model_dump()


def category_summary(date_from: str, date_to: str, account_id: str | None = None) -> dict[str, Any]:
    request = SpendingSummaryRequest(date_from=date_from, date_to=date_to, account_id=account_id)
    return _FINANCE_SERVICE.get_category_summary(request).model_dump()


def summary(
    period: str = "week",
    start_ts: str | None = None,
    end_ts: str | None = None,
    group_by: str = "category",
) -> dict[str, Any]:
    start, end = _period_bounds(period, start_ts, end_ts)
    if start is None or end is None:
        raise FinanceValidationError(f"Unsupported period '{period}'")
    items = _FINANCE_SERVICE.list_transactions(
        TransactionListFilters(
            date_from=_coerce_ts_to_date(start),
            date_to=_coerce_ts_to_date(end),
            limit=500,
        )
    ).results
    totals: dict[str, int] = {}
    for item in items:
        if group_by == "category":
            key = item.category_id
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
    finance_audit("finance_summary_requested", period=period)
    return report.model_dump()


def set_rule_threshold(rule_key: str, threshold_value: float, enabled: bool = True) -> dict[str, Any]:
    return _FINANCE_SERVICE.set_rule_threshold(rule_key, threshold_value, enabled)


def get_rule_thresholds() -> dict[str, dict[str, Any]]:
    return _FINANCE_SERVICE.get_rule_thresholds()


def generate_finance_brief(snapshot: dict[str, Any], now: datetime | None = None) -> dict[str, Any]:
    return _FINANCE_SERVICE.generate_brief(snapshot)


def list_alerts(limit: int = 100) -> list[dict[str, Any]]:
    response = _FINANCE_SERVICE.list_alerts(limit=limit)
    return [r.model_dump() for r in response.results]


def list_behavior_logs(limit: int = 100) -> list[dict[str, Any]]:
    return _FINANCE_SERVICE.list_behavior_logs(limit=limit)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

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
