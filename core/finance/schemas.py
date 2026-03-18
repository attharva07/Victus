from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .policy import FinanceValidationError

SUPPORTED_CURRENCIES = {"USD", "EUR", "GBP", "CAD", "AUD", "JPY"}
DEFAULT_CATEGORY = "uncategorized"

ACCOUNT_TYPES = Literal["cash", "checking", "savings", "credit", "wallet", "brokerage", "loan", "other"]
CATEGORY_TYPES = Literal["expense", "income", "transfer", "savings", "debt"]
DIRECTION_TYPES = Literal["expense", "income", "transfer", "refund"]
BUDGET_PERIODS = Literal["monthly"]
BILL_STATUSES = Literal["pending", "paid", "overdue", "cancelled"]
SAVINGS_STATUSES = Literal["active", "paused", "completed", "cancelled"]
ALERT_SEVERITIES = Literal["urgent", "caution", "advisory", "info"]
ALERT_STATUSES = Literal["active", "resolved", "dismissed"]


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = " ".join(value.strip().split())
    return normalized or None


def normalize_category(value: str | None) -> str:
    normalized = _normalize_text(value)
    if normalized is None:
        return DEFAULT_CATEGORY
    lowered = normalized.casefold().replace("&", " and ")
    parts = [part for part in lowered.replace("/", " ").replace("-", " ").split() if part]
    return "_".join(parts) if parts else DEFAULT_CATEGORY


def parse_amount_to_cents(value: Decimal | float | int | str) -> int:
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise FinanceValidationError("Amount must be a valid decimal value.") from exc
    if not decimal_value.is_finite():
        raise FinanceValidationError("Amount must be finite.")
    quantized = decimal_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if quantized == Decimal("0.00"):
        raise FinanceValidationError("Amount cannot be zero.")
    if abs(quantized) > Decimal("1000000000.00"):
        raise FinanceValidationError("Amount exceeds supported range.")
    return int(quantized * 100)


def _validate_iso_date(value: date | str | None, field_name: str, allow_none: bool = False) -> date | None:
    if value is None:
        if allow_none:
            return None
        return date.today()
    if isinstance(value, date):
        return value
    normalized = str(value).strip()
    if not normalized:
        return date.today() if not allow_none else None
    try:
        return date.fromisoformat(normalized)
    except ValueError as exc:
        raise FinanceValidationError(f"{field_name} must be a valid ISO date (YYYY-MM-DD).") from exc


# ===========================================================================
# A. LEDGER CORE — Accounts
# ===========================================================================

class AccountCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=120)
    account_type: ACCOUNT_TYPES
    currency: str = "USD"
    institution: str | None = Field(default=None, max_length=120)
    is_active: bool = True

    @field_validator("name", "institution")
    @classmethod
    def normalize_strings(cls, value: str | None) -> str | None:
        return _normalize_text(value)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        currency = value.strip().upper()
        if currency not in SUPPORTED_CURRENCIES:
            raise FinanceValidationError(f"Unsupported currency '{currency}'")
        return currency


class AccountUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, max_length=120)
    account_type: ACCOUNT_TYPES | None = None
    currency: str | None = None
    institution: str | None = Field(default=None, max_length=120)
    is_active: bool | None = None

    @field_validator("name", "institution", mode="before")
    @classmethod
    def normalize_strings(cls, value: str | None) -> str | None:
        return _normalize_text(value)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        if value is None:
            return None
        currency = value.strip().upper()
        if currency not in SUPPORTED_CURRENCIES:
            raise FinanceValidationError(f"Unsupported currency '{currency}'")
        return currency

    @model_validator(mode="after")
    def ensure_non_empty_update(self) -> "AccountUpdate":
        if not self.model_fields_set:
            raise FinanceValidationError("At least one account field must be supplied for update.")
        return self


class AccountRecord(BaseModel):
    id: str
    name: str
    account_type: str
    currency: str
    institution: str | None
    is_active: bool
    created_at: str
    updated_at: str


class AccountResponse(BaseModel):
    account: AccountRecord


class AccountsResponse(BaseModel):
    results: list[AccountRecord]
    count: int


# ===========================================================================
# A. LEDGER CORE — Categories
# ===========================================================================

class CategoryCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=120)
    type: CATEGORY_TYPES = "expense"
    parent_category: str | None = Field(default=None, max_length=120)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return normalize_category(value)


class CategoryUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, max_length=120)
    type: CATEGORY_TYPES | None = None
    parent_category: str | None = Field(default=None, max_length=120)

    @model_validator(mode="after")
    def ensure_non_empty_update(self) -> "CategoryUpdate":
        if not self.model_fields_set:
            raise FinanceValidationError("At least one category field must be supplied for update.")
        return self


class CategoryRecord(BaseModel):
    id: str
    name: str
    type: str
    parent_category: str | None
    is_system: bool
    is_active: bool
    created_at: str
    updated_at: str


class CategoriesResponse(BaseModel):
    results: list[CategoryRecord]
    count: int


# ===========================================================================
# A. LEDGER CORE — Transactions
# ===========================================================================

class TransactionWrite(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    amount: Decimal | float | int | str
    currency: str = "USD"
    category: str | None = DEFAULT_CATEGORY
    merchant: str | None = Field(default=None, max_length=160)
    notes: str | None = Field(default=None, max_length=1000)
    account_id: str | None = Field(default=None, max_length=80)
    direction: DIRECTION_TYPES = "expense"
    payment_method: str | None = Field(default=None, max_length=80)
    transaction_date: date | str = Field(default_factory=date.today)
    source: str = Field(default="user", max_length=80)
    tags: str | None = Field(default=None, max_length=500)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        currency = value.strip().upper()
        if currency not in SUPPORTED_CURRENCIES:
            raise FinanceValidationError(f"Unsupported currency '{currency}'")
        return currency

    @field_validator("merchant", "notes", "account_id", "payment_method", "source", "tags", mode="before")
    @classmethod
    def normalize_optional_fields(cls, value: str | None) -> str | None:
        return _normalize_text(value)

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category_value(cls, value: str | None) -> str:
        return normalize_category(value)

    @field_validator("transaction_date", mode="before")
    @classmethod
    def validate_transaction_date(cls, value: date | str | None) -> date:
        result = _validate_iso_date(value, "transaction_date")
        assert result is not None
        return result

    @property
    def amount_cents(self) -> int:
        return parse_amount_to_cents(self.amount)


class TransactionUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    amount: Decimal | float | int | str | None = None
    currency: str | None = None
    category: str | None = None
    merchant: str | None = Field(default=None, max_length=160)
    notes: str | None = Field(default=None, max_length=1000)
    account_id: str | None = Field(default=None, max_length=80)
    direction: DIRECTION_TYPES | None = None
    payment_method: str | None = Field(default=None, max_length=80)
    transaction_date: date | str | None = None
    tags: str | None = Field(default=None, max_length=500)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        if value is None:
            return None
        currency = value.strip().upper()
        if currency not in SUPPORTED_CURRENCIES:
            raise FinanceValidationError(f"Unsupported currency '{currency}'")
        return currency

    @field_validator("merchant", "notes", "account_id", "payment_method", "tags", mode="before")
    @classmethod
    def normalize_optional_fields(cls, value: str | None) -> str | None:
        return _normalize_text(value)

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category_value(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return normalize_category(value)

    @field_validator("transaction_date", mode="before")
    @classmethod
    def validate_transaction_date(cls, value: date | str | None) -> date | None:
        return _validate_iso_date(value, "transaction_date", allow_none=True)

    @model_validator(mode="after")
    def ensure_non_empty_update(self) -> "TransactionUpdate":
        if not self.model_fields_set:
            raise FinanceValidationError("At least one transaction field must be supplied for update.")
        return self

    @property
    def amount_cents(self) -> int | None:
        if self.amount is None:
            return None
        return parse_amount_to_cents(self.amount)


class TransactionRecord(BaseModel):
    id: str
    amount_cents: int
    currency: str
    merchant: str | None
    transaction_date: str
    category_id: str
    account_id: str | None
    direction: str
    payment_method: str | None
    notes: str | None
    source: str | None
    tags: str | None
    created_at: str
    updated_at: str


class TransactionListFilters(BaseModel):
    date_from: date | str | None = None
    date_to: date | str | None = None
    category: str | None = None
    account_id: str | None = None
    direction: DIRECTION_TYPES | None = None
    merchant: str | None = None
    limit: int = Field(default=50, ge=1, le=500)

    @field_validator("date_from", "date_to", mode="before")
    @classmethod
    def validate_dates(cls, value: date | str | None) -> date | None:
        return _validate_iso_date(value, "filter date", allow_none=True)

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category_filter(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return normalize_category(value)

    @field_validator("account_id", "merchant", mode="before")
    @classmethod
    def normalize_text_filter(cls, value: str | None) -> str | None:
        return _normalize_text(value)


class TransactionResponse(BaseModel):
    transaction: TransactionRecord


class TransactionsResponse(BaseModel):
    results: list[TransactionRecord]
    count: int


class DeleteResult(BaseModel):
    deleted: bool
    id: str


# ===========================================================================
# A. LEDGER CORE — Summaries
# ===========================================================================

class SpendingSummaryRequest(BaseModel):
    date_from: date | str
    date_to: date | str
    account_id: str | None = None

    @field_validator("date_from", "date_to", mode="before")
    @classmethod
    def validate_dates(cls, value: date | str) -> date:
        result = _validate_iso_date(value, "summary date")
        assert result is not None
        return result

    @field_validator("account_id", mode="before")
    @classmethod
    def normalize_account_filter(cls, value: str | None) -> str | None:
        return _normalize_text(value)

    @model_validator(mode="after")
    def validate_range(self) -> "SpendingSummaryRequest":
        if self.date_to < self.date_from:
            raise FinanceValidationError("date_to must be on or after date_from.")
        return self


class SummaryTotals(BaseModel):
    currency: str
    income_cents: int
    expense_cents: int
    net_cents: int
    transaction_count: int


class SpendingSummary(BaseModel):
    date_from: str
    date_to: str
    account_id: str | None
    totals: SummaryTotals
    by_category: dict[str, int]
    by_account: dict[str, int]
    by_merchant: dict[str, int]
    by_direction: dict[str, int]


class CategorySummary(BaseModel):
    date_from: str
    date_to: str
    account_id: str | None
    categories: list[dict[str, int | str]]


class AccountSummary(BaseModel):
    date_from: str
    date_to: str
    accounts: list[dict[str, int | str]]


# ===========================================================================
# B. BUDGETING
# ===========================================================================

class BudgetCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=120)
    category_id: str | None = Field(default=None, max_length=80)
    account_id: str | None = Field(default=None, max_length=80)
    amount_limit: Decimal | float | int | str
    currency: str = "USD"
    period: BUDGET_PERIODS = "monthly"
    warning_threshold_percent: int = Field(default=80, ge=1, le=100)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        result = _normalize_text(value)
        assert result is not None
        return result

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        currency = value.strip().upper()
        if currency not in SUPPORTED_CURRENCIES:
            raise FinanceValidationError(f"Unsupported currency '{currency}'")
        return currency

    @property
    def amount_limit_cents(self) -> int:
        cents = parse_amount_to_cents(self.amount_limit)
        if cents <= 0:
            raise FinanceValidationError("Budget amount must be positive.")
        return cents


class BudgetUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, max_length=120)
    category_id: str | None = Field(default=None, max_length=80)
    account_id: str | None = Field(default=None, max_length=80)
    amount_limit: Decimal | float | int | str | None = None
    currency: str | None = None
    period: BUDGET_PERIODS | None = None
    warning_threshold_percent: int | None = Field(default=None, ge=1, le=100)
    is_active: bool | None = None

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        if value is None:
            return None
        currency = value.strip().upper()
        if currency not in SUPPORTED_CURRENCIES:
            raise FinanceValidationError(f"Unsupported currency '{currency}'")
        return currency

    @model_validator(mode="after")
    def ensure_non_empty_update(self) -> "BudgetUpdate":
        if not self.model_fields_set:
            raise FinanceValidationError("At least one budget field must be supplied for update.")
        return self

    @property
    def amount_limit_cents(self) -> int | None:
        if self.amount_limit is None:
            return None
        cents = parse_amount_to_cents(self.amount_limit)
        if cents <= 0:
            raise FinanceValidationError("Budget amount must be positive.")
        return cents


class BudgetRecord(BaseModel):
    id: str
    name: str
    category_id: str | None
    account_id: str | None
    amount_limit_cents: int
    currency: str
    period: str
    warning_threshold_percent: int
    is_active: bool
    created_at: str
    updated_at: str


class BudgetStatusRecord(BaseModel):
    budget: BudgetRecord
    spent_cents: int
    remaining_cents: int
    usage_percent: float
    status: str  # "under", "warning", "exceeded"


class BudgetResponse(BaseModel):
    budget: BudgetRecord


class BudgetsResponse(BaseModel):
    results: list[BudgetRecord]
    count: int


class BudgetStatusResponse(BaseModel):
    results: list[BudgetStatusRecord]
    count: int


# ===========================================================================
# C. BILLS / OBLIGATIONS / REMINDERS
# ===========================================================================

class BillCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=160)
    amount_expected: Decimal | float | int | str | None = None
    currency: str = "USD"
    due_date: date | str
    recurrence_rule: str | None = Field(default=None, max_length=80)
    category_id: str | None = Field(default=None, max_length=80)
    account_id: str | None = Field(default=None, max_length=80)
    auto_reminder: bool = True
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("name", "notes", mode="before")
    @classmethod
    def normalize_strings(cls, value: str | None) -> str | None:
        return _normalize_text(value)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        currency = value.strip().upper()
        if currency not in SUPPORTED_CURRENCIES:
            raise FinanceValidationError(f"Unsupported currency '{currency}'")
        return currency

    @field_validator("due_date", mode="before")
    @classmethod
    def validate_due_date(cls, value: date | str) -> date:
        result = _validate_iso_date(value, "due_date")
        assert result is not None
        return result

    @field_validator("recurrence_rule", mode="before")
    @classmethod
    def validate_recurrence(cls, value: str | None) -> str | None:
        if value is None:
            return None
        allowed = {"monthly", "weekly", "biweekly", "quarterly", "annually"}
        normalized = value.strip().lower()
        if normalized not in allowed:
            raise FinanceValidationError(f"Invalid recurrence_rule '{value}'. Allowed: {', '.join(sorted(allowed))}")
        return normalized

    @property
    def amount_expected_cents(self) -> int | None:
        if self.amount_expected is None:
            return None
        return parse_amount_to_cents(self.amount_expected)


class BillUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, max_length=160)
    amount_expected: Decimal | float | int | str | None = None
    currency: str | None = None
    due_date: date | str | None = None
    recurrence_rule: str | None = Field(default=None, max_length=80)
    category_id: str | None = Field(default=None, max_length=80)
    account_id: str | None = Field(default=None, max_length=80)
    auto_reminder: bool | None = None
    notes: str | None = Field(default=None, max_length=1000)
    status: BILL_STATUSES | None = None

    @field_validator("due_date", mode="before")
    @classmethod
    def validate_due_date(cls, value: date | str | None) -> date | None:
        return _validate_iso_date(value, "due_date", allow_none=True)

    @model_validator(mode="after")
    def ensure_non_empty_update(self) -> "BillUpdate":
        if not self.model_fields_set:
            raise FinanceValidationError("At least one bill field must be supplied for update.")
        return self

    @property
    def amount_expected_cents(self) -> int | None:
        if self.amount_expected is None:
            return None
        return parse_amount_to_cents(self.amount_expected)


class BillRecord(BaseModel):
    id: str
    name: str
    amount_expected_cents: int | None
    currency: str
    due_date: str
    recurrence_rule: str | None
    category_id: str | None
    account_id: str | None
    status: str
    auto_reminder: bool
    notes: str | None
    created_at: str
    updated_at: str


class BillResponse(BaseModel):
    bill: BillRecord


class BillsResponse(BaseModel):
    results: list[BillRecord]
    count: int


# ===========================================================================
# D. SAVINGS GOALS
# ===========================================================================

class SavingsGoalCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=120)
    target_amount: Decimal | float | int | str
    currency: str = "USD"
    target_date: date | str | None = None
    linked_account_id: str | None = Field(default=None, max_length=80)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        result = _normalize_text(value)
        assert result is not None
        return result

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        currency = value.strip().upper()
        if currency not in SUPPORTED_CURRENCIES:
            raise FinanceValidationError(f"Unsupported currency '{currency}'")
        return currency

    @field_validator("target_date", mode="before")
    @classmethod
    def validate_target_date(cls, value: date | str | None) -> date | None:
        return _validate_iso_date(value, "target_date", allow_none=True)

    @property
    def target_amount_cents(self) -> int:
        cents = parse_amount_to_cents(self.target_amount)
        if cents <= 0:
            raise FinanceValidationError("Savings target amount must be positive.")
        return cents


class SavingsGoalUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, max_length=120)
    target_amount: Decimal | float | int | str | None = None
    currency: str | None = None
    target_date: date | str | None = None
    linked_account_id: str | None = Field(default=None, max_length=80)
    status: SAVINGS_STATUSES | None = None

    @field_validator("target_date", mode="before")
    @classmethod
    def validate_target_date(cls, value: date | str | None) -> date | None:
        return _validate_iso_date(value, "target_date", allow_none=True)

    @model_validator(mode="after")
    def ensure_non_empty_update(self) -> "SavingsGoalUpdate":
        if not self.model_fields_set:
            raise FinanceValidationError("At least one savings goal field must be supplied for update.")
        return self

    @property
    def target_amount_cents(self) -> int | None:
        if self.target_amount is None:
            return None
        cents = parse_amount_to_cents(self.target_amount)
        if cents <= 0:
            raise FinanceValidationError("Savings target amount must be positive.")
        return cents


class SavingsProgressUpdate(BaseModel):
    amount: Decimal | float | int | str
    source: str = Field(default="manual", max_length=80)

    @property
    def amount_cents(self) -> int:
        return parse_amount_to_cents(self.amount)


class SavingsGoalRecord(BaseModel):
    id: str
    name: str
    target_amount_cents: int
    currency: str
    target_date: str | None
    linked_account_id: str | None
    current_progress_cents: int
    status: str
    created_at: str
    updated_at: str


class SavingsStatusRecord(BaseModel):
    goal: SavingsGoalRecord
    remaining_cents: int
    progress_percent: float
    on_track: bool


class SavingsGoalResponse(BaseModel):
    goal: SavingsGoalRecord


class SavingsGoalsResponse(BaseModel):
    results: list[SavingsGoalRecord]
    count: int


class SavingsStatusResponse(BaseModel):
    results: list[SavingsStatusRecord]
    count: int


# ===========================================================================
# E. ALERTS
# ===========================================================================

class AlertRecord(BaseModel):
    id: str
    type: str
    severity: str
    title: str
    message: str
    source_rule: str
    related_entity_type: str | None
    related_entity_id: str | None
    created_at: str
    resolved_at: str | None
    status: str


class AlertsResponse(BaseModel):
    results: list[AlertRecord]
    count: int


# ===========================================================================
# F. INSIGHTS
# ===========================================================================

class InsightRecord(BaseModel):
    pattern: str
    score: float
    reason: str
    suggestion: str
    data_source: str


class InsightsResponse(BaseModel):
    results: list[InsightRecord]
    date_from: str
    date_to: str


# ===========================================================================
# G. GUIDANCE
# ===========================================================================

class GuidanceRecord(BaseModel):
    title: str
    message: str
    source: str
    severity: str
    traceable_basis: str


class GuidanceResponse(BaseModel):
    results: list[GuidanceRecord]
    count: int


# ===========================================================================
# Legacy compatibility schemas
# ===========================================================================

class LegacySummaryReport(BaseModel):
    period: str
    start_ts: str | None
    end_ts: str | None
    group_by: str
    totals: dict[str, int]


class AuditExpectation(BaseModel):
    event: str
    redacted_note_excerpt: str | None = None
    note_hash: str | None = None
