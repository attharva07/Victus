from __future__ import annotations

from typing import Any, Dict

from ..base import BasePlugin
from ...core.schemas import Approval, ExecutionError
from ...finance import service


class FinancePlugin(BasePlugin):
    def capabilities(self) -> Dict[str, Dict[str, Any]]:
        return {
            "add_transaction": {
                "date": "YYYY-MM-DD",
                "amount": "number",
                "category": "text",
                "note": "text (optional)",
            },
            "list_transactions": {"date_from": "YYYY-MM-DD", "date_to": "YYYY-MM-DD"},
            "month_summary": {"month": "YYYY-MM"},
            "export_logbook_md": {"range": "month|week|custom", "month": "YYYY-MM"},
        }

    def validate_args(self, action: str, args: Dict[str, Any]) -> None:
        if action == "add_transaction":
            if "amount" not in args or "category" not in args:
                raise ExecutionError("finance.add_transaction requires amount and category")
            return
        if action in {"list_transactions", "month_summary", "export_logbook_md"}:
            return
        raise ExecutionError(f"Unknown finance action '{action}'")

    def execute(self, action: str, args: Dict[str, Any], approval: Approval) -> Any:
        if not approval.policy_signature:
            raise ExecutionError("Missing policy signature")

        if action == "add_transaction":
            preview = self._preview_transaction(args)
            if not args.get("confirm", True):
                return {"preview": preview, "saved": False}
            transaction = service.add_transaction(
                date=args.get("date"),
                amount=float(args.get("amount")),
                category=str(args.get("category")),
                merchant=args.get("merchant"),
                note=args.get("note"),
                account=args.get("account"),
                payment_method=args.get("payment_method"),
                tags=args.get("tags"),
                source=args.get("source", "victus"),
            )
            return {"preview": preview, "saved": True, "transaction": transaction}
        if action == "list_transactions":
            return service.list_transactions(
                date_from=args.get("date_from"),
                date_to=args.get("date_to"),
                category=args.get("category"),
                account=args.get("account"),
            )
        if action == "month_summary":
            return service.month_summary(month=args.get("month"))
        if action == "export_logbook_md":
            return {
                "markdown": service.export_logbook_md(
                    range=args.get("range", "month"),
                    month=args.get("month"),
                )
            }
        raise ExecutionError(f"Unknown finance action '{action}'")

    @staticmethod
    def _preview_transaction(args: Dict[str, Any]) -> str:
        date = args.get("date") or "(today)"
        amount = args.get("amount")
        category = args.get("category")
        note = args.get("note") or ""
        return f"{date} | {amount} | {category} {note}".strip()
