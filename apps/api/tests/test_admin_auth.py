from __future__ import annotations

from fastapi.testclient import TestClient

from edb_api import auth
from edb_api.main import create_app

from .conftest import ORIGIN, PASSWORD
from .ts_contract import check


def login(client, password=PASSWORD, headers=ORIGIN):
    return client.post("/api/admin/login", json={"password": password}, headers=headers)


def test_session_reports_state(client):
    data = client.get("/api/admin/session").json()
    check(data, "AdminSession")
    assert data == {"authenticated": False, "configured": True, "steam": False, "password": True}


def test_protected_routes_require_login(client):
    for method, path in (("get", "/api/admin/overview"), ("get", "/api/admin/export/players.csv"),
                         ("post", "/api/admin/players"), ("get", "/api/admin/confront/candidates?season=1")):
        response = getattr(client, method)(path, **({"json": {}} if method == "post" else {}))
        assert response.status_code == 401, path
        assert "Sessão" in response.json()["detail"]


def test_login_sets_httponly_cookie_and_opens_admin(client):
    response = login(client)
    assert response.status_code == 200 and response.json() == {"ok": True}
    cookie = response.headers["set-cookie"]
    assert cookie.startswith("edb_admin=") and "HttpOnly" in cookie and "SameSite=lax" in cookie
    assert "Secure" not in cookie
    assert client.get("/api/admin/session").json()["authenticated"] is True
    check(client.get("/api/admin/overview").json(), "AdminOverview")


def test_cookie_is_secure_when_enabled(client, monkeypatch):
    monkeypatch.setenv("EDB_COOKIE_SECURE", "1")
    assert "Secure" in login(client).headers["set-cookie"]


def test_wrong_password(client):
    response = login(client, "errada")
    assert response.status_code == 401 and response.json()["detail"] == "Senha incorreta."
    assert client.get("/api/admin/session").json()["authenticated"] is False


def test_logout_clears_session(admin):
    assert admin.post("/api/admin/logout", headers=ORIGIN).json() == {"ok": True}
    assert admin.get("/api/admin/session").json()["authenticated"] is False
    assert admin.get("/api/admin/overview").status_code == 401


def test_session_expires(admin, monkeypatch):
    real_now = auth.now()
    monkeypatch.setattr(auth, "now", lambda: real_now + auth.SESSION_SECONDS + 5)
    assert admin.get("/api/admin/session").json()["authenticated"] is False
    assert admin.get("/api/admin/overview").status_code == 401


def test_tampered_or_foreign_tokens_are_rejected(client):
    good = auth.make_token()
    expiry, _, signature = good.partition(".")
    for bad in ("", "abc", expiry + ".", expiry + "." + signature[::-1], str(int(expiry) + 99999) + "." + signature):
        client.cookies.set("edb_admin", bad)
        assert client.get("/api/admin/session").json()["authenticated"] is False, bad
    client.cookies.set("edb_admin", good)
    assert client.get("/api/admin/session").json()["authenticated"] is True


def test_token_signed_with_another_secret_is_rejected(client, monkeypatch):
    token = auth.make_token()
    monkeypatch.setenv("EDB_SESSION_SECRET", "outro-segredo")
    client.cookies.set("edb_admin", token)
    assert client.get("/api/admin/session").json()["authenticated"] is False


def test_lockout_after_five_failures_and_recovery(client, monkeypatch):
    for _ in range(5):
        assert login(client, "errada").status_code == 401
    blocked = login(client, PASSWORD)
    assert blocked.status_code == 429 and "Muitas tentativas" in blocked.json()["detail"]
    start = auth.now()
    monkeypatch.setattr(auth, "now", lambda: start + auth.WINDOW_SECONDS + 1)
    assert login(client, PASSWORD).status_code == 200


def test_successful_login_resets_failure_counter(client):
    for _ in range(4):
        login(client, "errada")
    assert login(client).status_code == 200
    for _ in range(4):
        assert login(client, "errada").status_code == 401
    assert login(client).status_code == 200


def test_invalid_origin_is_blocked(client):
    assert login(client, headers={"Origin": "https://site-malicioso.example"}).status_code == 403
    assert login(client, headers={"Sec-Fetch-Site": "cross-site"}).status_code == 403
    assert login(client, headers={"Origin": "http://localhost:3000/"}).status_code == 200


def test_writes_check_origin_even_with_valid_session(admin):
    bad = {"Origin": "https://site-malicioso.example"}
    response = admin.post("/api/admin/players", json={"nickname": "X", "skill_level": 5}, headers=bad)
    assert response.status_code == 403
    assert admin.post("/api/admin/logout", headers=bad).status_code == 403
    assert admin.get("/api/admin/overview", headers=bad).status_code == 200  # leitura não muda dados


def test_unconfigured_password_blocks_admin(demo, monkeypatch):
    for value in ("", "SUBSTITUA-POR-UMA-SENHA-FORTE"):
        monkeypatch.setenv("XINXAS_ADMIN_PASSWORD", value)
        client = TestClient(create_app())
        assert client.get("/api/admin/session").json() == {"authenticated": False, "configured": False, "steam": False, "password": False}
        response = login(client, value or "x")
        assert response.status_code == 503 and "senha" in response.json()["detail"].lower()
        assert client.get("/api/admin/overview").status_code == 503


def test_forwarded_ip_only_trusted_when_enabled(client, monkeypatch):
    monkeypatch.setenv("EDB_TRUST_PROXY", "1")
    for _ in range(5):
        client.post("/api/admin/login", json={"password": "errada"},
                    headers={**ORIGIN, "X-Forwarded-For": "10.0.0.1"})
    assert client.post("/api/admin/login", json={"password": PASSWORD},
                       headers={**ORIGIN, "X-Forwarded-For": "10.0.0.1"}).status_code == 429
    assert client.post("/api/admin/login", json={"password": PASSWORD},
                       headers={**ORIGIN, "X-Forwarded-For": "10.0.0.2"}).status_code == 200
