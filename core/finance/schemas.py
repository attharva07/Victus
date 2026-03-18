from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .policy import FinanceValidationError

SUPPORTED_CURRENCIES = {"USD", "EUR", "GBP", "CAD", "AUD", "JPY"}
DEFAULT_CATEGORY = "uncategorized"


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


class AccountUpsert(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    id: str | None = None
    name: str = Field(min_length=1, max_length=120)
    account_type: Literal["checking", "savings", "credit", "cash", "brokerage", "loan", "other"]
    institution: str | None = Field(default=None, max_length=120)
    is_active: bool = True

    @field_validator("name", "institution")
    @classmethod
    def normalize_strings(cls, value: str | None) -> str | None:
        return _normalize_text(value)


class TransactionWrite(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    amount: Decimal | float | int | str
    currency: str = "USD"
    category: str | None = DEFAULT_CATEGORY
    merchant: str | None = Field(default=None, max_length=160)
    note: str | None = Field(default=None, max_length=1000)
    account_id: str | None = Field(default=None, max_length=80)
    method: str | None = Field(default=None, max_length=80)
    transaction_date: date | str = Field(default_factory=date.today)
    source: str = Field(default="user", max_length=80)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        currency = value.strip().upper()
        if currency not in SUPPORTED_CURRENCIES:
            raise FinanceValidationError(f"Unsupported currency '{currency}'")
        return currency

    @field_validator("merchant", "note", "account_id", "method", "source", mode="before")
    @classmethod
    def normalize_optional_fields(cls, value: str | None) -> str | None:
        return _normalize_text(value)

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category_value(cls, value: str | None) -> str:
        return normalize_category(value)

    @field_validator("transaction_date", mode="before")
    @classmethod
    def validate_transaction_date(cls, value: date | str) -> date:
        if isinstance(value, date):
            return value
        try:
            return date.fromisoformat(str(value))
        except ValueError as exc:
            raise FinanceValidationError("transaction_date must be a valid ISO date (YYYY-MM-DD).") from exc

    @property
    def amount_cents(self) -> int:
        return parse_amount_to_cents(self.amount)


class TransactionUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    amount: Decimal | float | int | str | None = None
    currency: str | None = None
    category: str | None = None
    merchant: str | None = Field(default=None, max_length=160)
    note: str | None = Field(default=None, max_length=1000)
    account_id: str | None = Field(default=None, max_length=80)
    method: str | None = Field(default=None, max_length=80)
    transaction_date: date | str | None = None

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        if value is None:
            return None
        currency = value.strip().upper()
        if currency not in SUPPORTED_CURRENCIES:
            raise FinanceValidationError(f"Unsupported currency '{currency}'")
        return currency

    @field_validator("merchant", "note", "account_id", "method", mode="before")
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
        if value is None or isinstance(value, date):
            return value
        try:
            return date.fromisoformat(str(value))
        except ValueError as exc:
            raise FinanceValidationError("transaction_date must be a valid ISO date (YYYY-MM-DD).") from exc

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
    transaction_date: str
    amount_cents: int
    currency: str
    category: str
    merchant: str | None
    note: str | None
    account_id: str | None
    method: str | None
    source: str
    created_at: str
    updated_at: str


class TransactionListFilters(BaseModel):
    date_from: date | str | None = None
    date_to: date | str | None = None
    category: str | None = None
    account_id: str | None = None
    limit: int = Field(default=50, ge=1, le=500)

    @field_validator("date_from", "date_to", mode="before")
    @classmethod
    def validate_dates(cls, value: date | str | None) -> date | None:
        if value is None or isinstance(value, date):
            return value
        try:
            return date.fromisoformat(str(value))
        except ValueError as exc:
            raise FinanceValidationError("Filter dates must use YYYY-MM-DD.") from exc

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category_filter(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return normalize_category(value)

    @field_validator("account_id", mode="before")
    @classmethod
    def normalize_account_filter(cls, value: str | None) -> str | None:
        return _normalize_text(value)


class SpendingSummaryRequest(BaseModel):
    date_from: date | str
    date_to: date | str
    account_id: str | None = None

    @field_validator("date_from", "date_to", mode="before")
    @classmethod
    def validate_dates(cls, value: date | str) -> date:
        if isinstance(value, date):
            return value
        try:
            return date.fromisoformat(str(value))
        except ValueError as exc:
            raise FinanceValidationError("Summary dates must use YYYY-MM-DD.") from exc

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


class CategorySummary(BaseModel):
    date_from: str
    date_to: str
    account_id: str | None
    categories: list[dict[str, int | str]]


class DeleteResult(BaseModel):
    deleted: bool
    transaction_id: str


class TransactionResponse(BaseModel):
    transaction: TransactionRecord


class TransactionsResponse(BaseModel):
    results: list[TransactionRecord]
    count: int


class AccountRecord(BaseModel):
    id: str
    name: str
    account_type: str
    institution: str | None
    is_active: bool
    created_at: str


class AccountResponse(BaseModel):
    account: AccountRecord


class AuditExpectation(BaseModel):
    event: str
    redacted_note_excerpt: str | None = None
    note_hash: str | None = None


class LegacySummaryReport(BaseModel):
    period: str
    start_ts: str | None
    end_ts: str | None
    group_by: str
    totals: dict[str, int]
