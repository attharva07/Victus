from __future__ import annotations

from core.orchestrator.service import OrchestratorService
from core.registry.action_registry import ACTION_REGISTRY


def test_orchestrator_executes_registered_action(monkeypatch, tmp_path):
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv(
        "VICTUS_ENABLED_TOOLS",
        "finance.add_transaction,finance.list_transactions,memory.create_note,memory.search,mail.list_threads,mail.summarize_thread,files.create_workspace,files.generate_project_scaffold",
    )
    service = OrchestratorService()

    payload = {
        "request_id": "req-1",
        "intent": {
            "action": "finance.add_transaction",
            "parameters": {"amount": 6, "merchant": "Starbucks"},
            "context": {"user_id": "atharva", "source": "mobile"},
        },
    }
    result = service.execute(payload)

    assert result.executed is True
    assert result.status == "success"
    assert result.actions[0]["action"] == "finance.add_transaction"
    assert result.actions[0]["result"]["transaction_id"]


def test_orchestrator_unknown_action_fails_closed():
    service = OrchestratorService()
    result = service.execute(
        {
            "request_id": "req-2",
            "intent": {"action": "finance.delete_bank", "parameters": {}, "context": {"user_id": "u"}},
        }
    )
    assert result.executed is False
    assert result.error and result.error.code == "UNKNOWN_ACTION"


def test_orchestrator_missing_handler_fails_closed(monkeypatch):
    service = OrchestratorService()
    monkeypatch.setitem(ACTION_REGISTRY, "finance.add_transaction", None)
    result = service.execute(
        {
            "request_id": "req-3",
            "intent": {
                "action": "finance.add_transaction",
                "parameters": {"amount": 7, "merchant": "Coffee"},
                "context": {"user_id": "u"},
            },
        }
    )
    assert result.executed is False
    assert result.error and result.error.code == "MISSING_HANDLER"


def test_orchestrator_invalid_params_fails_closed(monkeypatch):
    monkeypatch.setenv("VICTUS_ENABLED_TOOLS", "finance.add_transaction")
    service = OrchestratorService()
    result = service.execute(
        {
            "request_id": "req-4",
            "intent": {
                "action": "finance.add_transaction",
                "parameters": {"merchant": "Coffee"},
                "context": {"user_id": "u"},
            },
        }
    )
    assert result.executed is False
    assert result.error and result.error.code == "EXECUTION_FAILED"


def test_orchestrator_policy_denial(monkeypatch):
    monkeypatch.setenv("VICTUS_ENABLED_TOOLS", "memory.create_note")
    service = OrchestratorService()
    result = service.execute(
        {
            "request_id": "req-5",
            "intent": {
                "action": "finance.add_transaction",
                "parameters": {"amount": 5, "merchant": "Cafe"},
                "context": {"user_id": "u"},
            },
        }
    )
    assert result.executed is False
    assert result.error and result.error.code == "POLICY_DENIED"
