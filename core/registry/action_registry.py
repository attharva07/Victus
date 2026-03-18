from __future__ import annotations

from collections.abc import Callable
from typing import Any

from core.domains.files.handlers import create_workspace_handler, generate_project_scaffold_handler
from core.domains.finance.handlers import (
    add_transaction_handler,
    create_account_handler,
    create_bill_handler,
    create_budget_handler,
    create_savings_goal_handler,
    get_budget_status_handler,
    get_category_summary_handler,
    get_due_bills_handler,
    get_guidance_handler,
    get_insights_handler,
    get_savings_status_handler,
    get_spending_summary_handler,
    list_accounts_handler,
    list_alerts_handler,
    list_bills_handler,
    list_budgets_handler,
    list_savings_goals_handler,
    list_transactions_handler,
    mark_bill_paid_handler,
)
from core.domains.mail.handlers import list_threads_handler, summarize_thread_handler
from core.domains.memory.handlers import create_note_handler, search_handler

ActionHandler = Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]

ACTION_REGISTRY: dict[str, ActionHandler | None] = {
    # Ledger
    "finance.add_transaction": add_transaction_handler,
    "finance.list_transactions": list_transactions_handler,
    "finance.get_spending_summary": get_spending_summary_handler,
    "finance.get_category_summary": get_category_summary_handler,
    # Accounts
    "finance.create_account": create_account_handler,
    "finance.list_accounts": list_accounts_handler,
    # Budgets
    "finance.create_budget": create_budget_handler,
    "finance.list_budgets": list_budgets_handler,
    "finance.get_budget_status": get_budget_status_handler,
    # Bills
    "finance.create_bill": create_bill_handler,
    "finance.list_bills": list_bills_handler,
    "finance.get_due_bills": get_due_bills_handler,
    "finance.mark_bill_paid": mark_bill_paid_handler,
    # Savings
    "finance.create_savings_goal": create_savings_goal_handler,
    "finance.list_savings_goals": list_savings_goals_handler,
    "finance.get_savings_status": get_savings_status_handler,
    # Alerts / Insights / Guidance
    "finance.list_alerts": list_alerts_handler,
    "finance.get_insights": get_insights_handler,
    "finance.get_guidance": get_guidance_handler,
    # Memory
    "memory.create_note": create_note_handler,
    "memory.search": search_handler,
    # Mail
    "mail.list_threads": list_threads_handler,
    "mail.summarize_thread": summarize_thread_handler,
    # Files
    "files.create_workspace": create_workspace_handler,
    "files.generate_project_scaffold": generate_project_scaffold_handler,
}
