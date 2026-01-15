from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel, Field

from victus.finance import service

router = APIRouter()


class TransactionRequest(BaseModel):
    date: Optional[str] = None
    amount: float
    category: str
    merchant: Optional[str] = None
    note: Optional[str] = None
    account: Optional[str] = None
    payment_method: Optional[str] = None
    tags: Optional[str] = None
    source: str = Field(default="manual")


@router.get("/api/finance/summary")
async def finance_summary(month: Optional[str] = None) -> dict:
    return service.month_summary(month=month)


@router.post("/api/finance/transaction")
async def finance_add_transaction(payload: TransactionRequest = Body(...)) -> dict:
    date = payload.date or datetime.utcnow().strftime("%Y-%m-%d")
    if not payload.category.strip():
        raise HTTPException(status_code=400, detail="Category is required")
    if payload.amount == 0:
        raise HTTPException(status_code=400, detail="Amount cannot be zero")
    preview = f"{date} | {payload.amount:.2f} | {payload.category}"
    transaction = service.add_transaction(
        date=date,
        amount=payload.amount,
        category=payload.category,
        merchant=payload.merchant,
        note=payload.note,
        account=payload.account,
        payment_method=payload.payment_method,
        tags=payload.tags,
        source=payload.source,
    )
    return {"preview": preview, "transaction": transaction}


@router.get("/api/finance/export")
async def finance_export(range: str = "month", month: Optional[str] = None) -> dict:
    if range not in {"month", "week", "custom"}:
        raise HTTPException(status_code=400, detail="Unsupported range")
    markdown = service.export_logbook_md(range=range, month=month)
    return {"markdown": markdown}
