from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Account:
    id: str
    name: str
    account_type: str
    currency: str
    institution: str | None
    is_active: bool
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class Category:
    id: str
    name: str
    type: str
    parent_category: str | None
    is_system: bool
    is_active: bool
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class Transaction:
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


@dataclass(frozen=True)
class Budget:
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


@dataclass(frozen=True)
class Bill:
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


@dataclass(frozen=True)
class SavingsGoal:
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


@dataclass(frozen=True)
class Alert:
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
