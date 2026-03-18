from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Account:
    id: str
    name: str
    account_type: str
    institution: str | None
    is_active: bool
    created_at: str


@dataclass(frozen=True)
class Category:
    key: str
    display_name: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class Transaction:
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
