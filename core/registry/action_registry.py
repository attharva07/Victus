from __future__ import annotations

from collections.abc import Callable
from typing import Any

from core.domains.files.handlers import create_workspace_handler, generate_project_scaffold_handler
from core.domains.finance.handlers import add_transaction_handler, list_transactions_handler
from core.domains.mail.handlers import list_threads_handler, summarize_thread_handler
from core.domains.memory.handlers import create_note_handler, search_handler

ActionHandler = Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]

ACTION_REGISTRY: dict[str, ActionHandler | None] = {
    "finance.add_transaction": add_transaction_handler,
    "finance.list_transactions": list_transactions_handler,
    "memory.create_note": create_note_handler,
    "memory.search": search_handler,
    "mail.list_threads": list_threads_handler,
    "mail.summarize_thread": summarize_thread_handler,
    "files.create_workspace": create_workspace_handler,
    "files.generate_project_scaffold": generate_project_scaffold_handler,
}
