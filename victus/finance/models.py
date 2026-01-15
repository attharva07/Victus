from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Transaction:
    id: int
    ts: str
    date: str
    amount: float
    category: str
    merchant: Optional[str]
    note: Optional[str]
    account: Optional[str]
    payment_method: Optional[str]
    tags: Optional[str]
    source: str


@dataclass
class Paycheck:
    id: int
    pay_date: str
    amount: float
    note: Optional[str]


@dataclass
class Budget:
    id: int
    month: str
    category: str
    limit_amount: float
