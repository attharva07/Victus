from __future__ import annotations

from core.errors import VictusError


ALLOWED_MEMORY_ACTIONS = {
    "write_memory",
    "search_memories",
    "list_recent",
    "get_memory_by_id",
    "delete_memory",
}

SENSITIVE_MEMORY_ACTIONS = {"delete_memory"}


class MemoryPolicyError(VictusError):
    pass


class MemoryValidationError(VictusError):
    pass


class MemoryNotFoundError(VictusError):
    pass


def enforce_memory_policy(action: str) -> None:
    if action not in ALLOWED_MEMORY_ACTIONS:
        raise MemoryPolicyError(f"Memory action '{action}' is not permitted.")
