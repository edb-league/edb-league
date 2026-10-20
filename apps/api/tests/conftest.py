from __future__ import annotations

import warnings

import pytest

warnings.filterwarnings("ignore")

from fastapi.testclient import TestClient  # noqa: E402

from edb_api import auth, service  # noqa: E402
from edb_api.main import create_app  # noqa: E402
from edb_api.service import LeagueService  # noqa: E402
from edb.storage import Store  # noqa: E402

PASSWORD = "senha-de-teste-123"
ORIGIN = {"Origin": "http://localhost:3000"}


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in ("EDB_DEMO", "EDB_TODAY", "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY",
                 "EDB_SESSION_SECRET", "EDB_COOKIE_SECURE", "EDB_TRUST_PROXY", "STEAM_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("XINXAS_ADMIN_PASSWORD", PASSWORD)
    monkeypatch.setenv("EDB_ALLOWED_ORIGINS", "http://localhost:3000")
    auth.reset_state()
    service.reset_service(None)
    yield
    service.reset_service(None)
    auth.reset_state()


@pytest.fixture
def demo(monkeypatch):
    monkeypatch.setenv("EDB_DEMO", "1")
    service.reset_service(None)
    return service.get_service()


@pytest.fixture
def client(demo):
    return TestClient(create_app())


@pytest.fixture
def admin(client):
    response = client.post("/api/admin/login", json={"password": PASSWORD}, headers=ORIGIN)
    assert response.status_code == 200, response.text
    return client


@pytest.fixture
def local(tmp_path):
    """Serviço com SQLite temporário e sem dados."""
    store = Store(db_file=tmp_path / "teste.db")
    svc = LeagueService(store)
    service.reset_service(svc)
    return svc


@pytest.fixture
def local_client(local):
    return TestClient(create_app())


@pytest.fixture
def local_admin(local_client):
    response = local_client.post("/api/admin/login", json={"password": PASSWORD}, headers=ORIGIN)
    assert response.status_code == 200
    return local_client
