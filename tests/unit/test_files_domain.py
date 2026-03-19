"""
Unit tests for the Files domain.

Covers: entities, schemas, policy, sandbox, service, handlers.
"""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# A. Entities
# ---------------------------------------------------------------------------


def test_sandbox_file_entity_is_frozen() -> None:
    from core.filesystem.entities import SandboxFile

    f = SandboxFile(path="notes.txt", size_bytes=100, extension=".txt")
    assert f.path == "notes.txt"
    with pytest.raises((AttributeError, TypeError)):
        f.path = "other.txt"  # type: ignore[misc]


def test_sandbox_file_content_entity() -> None:
    from core.filesystem.entities import SandboxFileContent

    fc = SandboxFileContent(path="readme.md", content="# Hello", size_bytes=7)
    assert fc.content == "# Hello"


# ---------------------------------------------------------------------------
# B. Schemas
# ---------------------------------------------------------------------------


def test_file_write_schema_valid() -> None:
    from core.filesystem.schemas import FileWriteRequest

    req = FileWriteRequest(path="notes.txt", content="hello", mode="overwrite")
    assert req.path == "notes.txt"
    assert req.mode == "overwrite"


def test_file_write_schema_default_mode() -> None:
    from core.filesystem.schemas import FileWriteRequest

    req = FileWriteRequest(path="file.md", content="x")
    assert req.mode == "overwrite"


def test_file_write_schema_rejects_invalid_mode() -> None:
    from core.filesystem.schemas import FileWriteRequest
    import pydantic

    with pytest.raises((pydantic.ValidationError, ValueError)):
        FileWriteRequest(path="file.txt", content="x", mode="truncate")


def test_file_write_schema_rejects_empty_path() -> None:
    from core.filesystem.schemas import FileWriteRequest
    import pydantic

    with pytest.raises((pydantic.ValidationError, ValueError)):
        FileWriteRequest(path="", content="x")


# ---------------------------------------------------------------------------
# C. Policy
# ---------------------------------------------------------------------------


def test_files_policy_allows_valid_actions() -> None:
    from core.filesystem.policy import enforce_files_policy

    for action in ("list_files", "read_file", "write_file", "delete_file", "create_workspace", "generate_scaffold"):
        enforce_files_policy(action)  # must not raise


def test_files_policy_blocks_unknown_action() -> None:
    from core.filesystem.policy import FilesPolicyError, enforce_files_policy

    with pytest.raises(FilesPolicyError):
        enforce_files_policy("execute_shell")


# ---------------------------------------------------------------------------
# D. Sandbox — path traversal, extensions, read/write/delete
# ---------------------------------------------------------------------------


def test_sandbox_blocks_path_traversal(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    from core.filesystem import sandbox
    importlib.reload(sandbox)

    with pytest.raises(sandbox.FileSandboxError):
        sandbox.write_file("../escape.txt", "bad", "overwrite")


def test_sandbox_blocks_disallowed_extension(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    from core.filesystem import sandbox
    importlib.reload(sandbox)

    with pytest.raises(sandbox.FileSandboxError):
        sandbox.write_file("malware.exe", "bad", "overwrite")


def test_sandbox_write_and_read(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    from core.filesystem import sandbox
    importlib.reload(sandbox)

    sandbox.write_file("hello.txt", "hello world", "overwrite")
    content = sandbox.read_file("hello.txt")
    assert content == "hello world"


def test_sandbox_append_mode(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    from core.filesystem import sandbox
    importlib.reload(sandbox)

    sandbox.write_file("log.txt", "line1\n", "overwrite")
    sandbox.write_file("log.txt", "line2\n", "append")
    content = sandbox.read_file("log.txt")
    assert "line1" in content
    assert "line2" in content


def test_sandbox_list_files(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    from core.filesystem import sandbox
    importlib.reload(sandbox)

    sandbox.write_file("a.txt", "a", "overwrite")
    sandbox.write_file("b.md", "b", "overwrite")
    files = sandbox.list_files()
    assert "a.txt" in files
    assert "b.md" in files


def test_sandbox_delete_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    from core.filesystem import sandbox
    importlib.reload(sandbox)

    sandbox.write_file("temp.txt", "temporary", "overwrite")
    assert "temp.txt" in sandbox.list_files()
    deleted = sandbox.delete_file("temp.txt")
    assert deleted is True
    assert "temp.txt" not in sandbox.list_files()


def test_sandbox_delete_nonexistent_returns_false(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    from core.filesystem import sandbox
    importlib.reload(sandbox)

    result = sandbox.delete_file("doesnotexist.txt")
    assert result is False


def test_sandbox_read_nonexistent_raises(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    from core.filesystem import sandbox
    importlib.reload(sandbox)

    with pytest.raises(sandbox.FileSandboxError):
        sandbox.read_file("ghost.txt")


# ---------------------------------------------------------------------------
# E. Handlers
# ---------------------------------------------------------------------------


def test_list_files_handler(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    from core.domains.files import handlers
    importlib.reload(handlers)

    result = handlers.list_files_handler({}, {})
    assert "files" in result
    assert "count" in result


def test_write_file_handler(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    from core.domains.files import handlers
    importlib.reload(handlers)

    result = handlers.write_file_handler(
        {"path": "test.txt", "content": "handler write", "mode": "overwrite"}, {}
    )
    assert result["ok"] is True


def test_read_file_handler(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    from core.domains.files import handlers
    importlib.reload(handlers)

    handlers.write_file_handler({"path": "read_test.txt", "content": "readable"}, {})
    result = handlers.read_file_handler({"path": "read_test.txt"}, {})
    assert result["content"] == "readable"


def test_delete_file_handler(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    from core.domains.files import handlers
    importlib.reload(handlers)

    handlers.write_file_handler({"path": "delete_me.txt", "content": "bye"}, {})
    result = handlers.delete_file_handler({"path": "delete_me.txt"}, {})
    assert result["deleted"] is True


def test_write_handler_blocks_traversal(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    from core.domains.files import handlers
    importlib.reload(handlers)

    with pytest.raises(ValueError):
        handlers.write_file_handler({"path": "../escape.txt", "content": "nope"}, {})


def test_write_handler_blocks_invalid_mode(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    from core.domains.files import handlers
    importlib.reload(handlers)

    with pytest.raises(ValueError):
        handlers.write_file_handler({"path": "file.txt", "content": "x", "mode": "truncate"}, {})


def test_create_workspace_and_scaffold(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    from core.domains.files import handlers
    importlib.reload(handlers)

    ws = handlers.create_workspace_handler({"name": "myproject"}, {})
    assert ws["workspace"] == "myproject"

    scaffold = handlers.generate_project_scaffold_handler({"workspace": "myproject"}, {})
    assert "README.md" in scaffold["created_files"]
    assert "src/main.py" in scaffold["created_files"]


def test_scaffold_requires_existing_workspace(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    from core.domains.files import handlers
    importlib.reload(handlers)

    with pytest.raises(ValueError):
        handlers.generate_project_scaffold_handler({"workspace": "nonexistent"}, {})
