from __future__ import annotations

from core.errors import VictusError


ALLOWED_FILES_ACTIONS = {
    "list_files",
    "read_file",
    "write_file",
    "delete_file",
    "create_workspace",
    "generate_scaffold",
}

DESTRUCTIVE_FILES_ACTIONS = {"delete_file"}


class FilesPolicyError(VictusError):
    pass


class FilesValidationError(VictusError):
    pass


def enforce_files_policy(action: str) -> None:
    if action not in ALLOWED_FILES_ACTIONS:
        raise FilesPolicyError(f"Files action '{action}' is not permitted.")
