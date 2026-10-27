from __future__ import annotations

from pathlib import Path

import pytest


def _clear_router_cache() -> None:
    try:
        import core.orchestrator.deterministic as deterministic
    except ModuleNotFoundError:
        # The orchestrator cannot be imported on checkouts that are missing core.signals /
        # victus.core.confidence. Those tests skip themselves; the language layer does not need it.
        return
    deterministic._router_confidence_components.cache_clear()


@pytest.fixture()
def lang_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Isolated data dir + DB for the language layer and orchestrator tests."""
    monkeypatch.setenv("VICTUS_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("VICTUS_ENABLED_TOOLS", raising=False)
    monkeypatch.delenv("VICTUS_LLM_ENABLED", raising=False)
    monkeypatch.delenv("VICTUS_ENABLE_LLM_FALLBACK", raising=False)

    import core.storage.db as db_module

    db_module._DB_INITIALIZED.clear()
    _clear_router_cache()
    yield tmp_path
    db_module._DB_INITIALIZED.clear()
    _clear_router_cache()
