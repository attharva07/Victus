from __future__ import annotations

from core.filesystem.sandbox import delete_file as _sandbox_delete
from core.filesystem.sandbox import list_files as _sandbox_list
from core.filesystem.sandbox import read_file as _sandbox_read
from core.filesystem.sandbox import write_file as _sandbox_write
from core.logging.audit import audit_event


def list_sandbox_files() -> list[str]:
    files = _sandbox_list()
    audit_event("files_listed", count=len(files))
    return files


def read_sandbox_file(path: str) -> str:
    content = _sandbox_read(path)
    audit_event("files_read", path=path)
    return content


def write_sandbox_file(path: str, content: str, mode: str = "overwrite") -> None:
    _sandbox_write(path, content, mode)
    audit_event("files_written", path=path, mode=mode, size=len(content))


def delete_sandbox_file(path: str) -> bool:
    deleted = _sandbox_delete(path)
    audit_event("files_deleted", path=path, deleted=deleted)
    return deleted
