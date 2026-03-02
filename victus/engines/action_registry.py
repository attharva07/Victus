from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from core.finance.service import add_transaction, list_transactions


@dataclass(frozen=True)
class ActionSpec:
    required_inputs: tuple[str, ...]
    executor: Callable[[dict[str, Any]], dict[str, Any]]


def _exec_finance_add_transaction(parameters: dict[str, Any]) -> dict[str, Any]:
    amount_value = float(parameters["amount"])
    amount_cents = int(round(amount_value * 100))
    transaction_id = add_transaction(
        amount_cents=amount_cents,
        category=str(parameters.get("category") or "uncategorized"),
        merchant=parameters.get("merchant"),
        note=parameters.get("note"),
        source=str(parameters.get("source") or "orchestrate_v2"),
    )
    return {"id": transaction_id, "amount_cents": amount_cents}


def _exec_finance_list_transactions(parameters: dict[str, Any]) -> dict[str, Any]:
    results = list_transactions(
        category=parameters.get("category"),
        limit=int(parameters.get("limit", 50)),
    )
    return {"results": results}


def _exec_reminder_add(parameters: dict[str, Any]) -> dict[str, Any]:
    return {"status": "queued", "title": parameters.get("title", "reminder")}


def _exec_memory_search(parameters: dict[str, Any]) -> dict[str, Any]:
    return {"status": "queued", "query": parameters.get("query", "")}


class ActionRegistry:
    _ACTIONS: dict[str, ActionSpec] = {
        "finance.add_transaction": ActionSpec(required_inputs=("amount",), executor=_exec_finance_add_transaction),
        "finance.list_transactions": ActionSpec(required_inputs=(), executor=_exec_finance_list_transactions),
        "reminder.add": ActionSpec(required_inputs=("title",), executor=_exec_reminder_add),
        "memory.search": ActionSpec(required_inputs=("query",), executor=_exec_memory_search),
    }

    @classmethod
    def get(cls, action: str) -> ActionSpec | None:
        return cls._ACTIONS.get(action)

    @classmethod
    def exists(cls, action: str) -> bool:
        return action in cls._ACTIONS

    @classmethod
    def list_actions(cls) -> list[str]:
        return sorted(cls._ACTIONS.keys())
