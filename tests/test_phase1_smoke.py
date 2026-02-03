import pytest
from fastapi.testclient import TestClient

from core.config import get_data_dir, get_vault_dir
from core.vault.sandbox import VaultPathError, safe_join


@pytest.fixture()
def temp_data_dir(tmp_path, monkeypatch):
    data_dir = tmp_path / "victus_data"
    monkeypatch.setenv("VICTUS_DATA_DIR", str(data_dir))
    yield data_dir
    monkeypatch.delenv("VICTUS_DATA_DIR", raising=False)


def test_data_dir_creation(temp_data_dir):
    data_dir = get_data_dir()
    assert data_dir.exists()
    assert data_dir == temp_data_dir


def test_vault_safe_join_blocks_traversal(temp_data_dir):
    vault_dir = get_vault_dir()
    with pytest.raises(VaultPathError):
        safe_join(vault_dir, "../secrets.txt")


def test_health_no_auth(temp_data_dir):
    from apps.local.main import app

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_me_requires_auth(temp_data_dir):
    from apps.local.main import app

    client = TestClient(app)
    response = client.get("/me")
    assert response.status_code == 401


def test_orchestrate_response(temp_data_dir):
    from apps.local.main import app

    client = TestClient(app)
    login = client.post("/login", json={"username": "admin", "password": "admin"})
    assert login.status_code == 200
    token = login.json()["token"]
    response = client.post(
        "/orchestrate",
        json={"text": "status"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "intent" in payload
    assert "actions_taken" in payload
    assert "message" in payload
