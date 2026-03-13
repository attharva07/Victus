from __future__ import annotations

from core.domains.files.handlers import create_workspace_handler, generate_project_scaffold_handler
from core.domains.finance.handlers import add_transaction_handler, list_transactions_handler
from core.domains.mail.handlers import list_threads_handler, summarize_thread_handler
from core.domains.memory.handlers import create_note_handler, search_handler
from core.logging.sanitizer import sanitize_payload


def test_log_sanitizer_redacts_sensitive_patterns():
    payload = {
        "authorization": "Bearer abc.def.ghi",
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.abc123.def456",
        "note": "api_key=sk-1234567890abcdefghijklmnop",
        "password": "topsecret",
    }
    sanitized = sanitize_payload(payload)
    assert sanitized["authorization"] == "[REDACTED]"
    assert sanitized["token"] == "[REDACTED]"
    assert "[REDACTED]" in sanitized["note"]
    assert sanitized["password"] == "[REDACTED]"


def test_finance_add_and_list_work(monkeypatch, tmp_path):
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    add_result = add_transaction_handler({"amount": 8.5, "merchant": "Bakery"}, {"user_id": "atharva"})
    assert add_result["transaction_id"]
    listed = list_transactions_handler({"limit": 5}, {})
    assert listed["count"] >= 1


def test_memory_create_and_search_work(monkeypatch, tmp_path):
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    created = create_note_handler({"content": "remember starbucks"}, {"user_id": "atharva"})
    assert created["memory_id"]
    searched = search_handler({"query": "starbucks", "limit": 5}, {})
    assert searched["count"] >= 1


def test_files_workspace_and_scaffold_work(monkeypatch, tmp_path):
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    created = create_workspace_handler({"name": "demo"}, {})
    assert created["workspace"] == "demo"
    scaffold = generate_project_scaffold_handler({"workspace": "demo"}, {})
    assert "README.md" in scaffold["created_files"]


def test_mail_handlers_return_clear_not_integrated_behavior():
    listed = list_threads_handler({}, {})
    assert listed["integration_status"] == "not_configured"
    summarized = summarize_thread_handler({"thread_id": "t-1"}, {})
    assert summarized["integration_status"] == "not_configured"
