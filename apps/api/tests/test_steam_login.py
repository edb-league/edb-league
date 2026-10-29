"""Login com a Steam: o que é aceito, o que é recusado e o que cada tipo de pessoa pode fazer."""
from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient

from edb_api import steam_openid
from edb_api.main import create_app

from .conftest import ORIGIN

SECRET = "segredo-de-teste-com-mais-de-16-caracteres"
SITE = "http://localhost:3000"
PLAYER = "76561198000000101"   # jogador da demonstração
STRANGER = "76561198000009999"  # não está cadastrado
ADMIN = "76561198000008888"     # só admin, fora do elenco


@pytest.fixture
def steam(demo, monkeypatch):
    monkeypatch.setenv("EDB_SESSION_SECRET", SECRET)
    monkeypatch.setenv("EDB_ADMIN_STEAMID", ADMIN)
    monkeypatch.setattr(steam_openid, "check_with_steam", lambda params, timeout=6.0: True)
    steam_openid.reset_state()
    return TestClient(create_app(), follow_redirects=False)


def nonce(offset: int = 0) -> str:
    return datetime.fromtimestamp(datetime.now(timezone.utc).timestamp() + offset, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") + "abc"


def start(client, next_path="/rankings/elite"):
    response = client.get("/api/auth/steam/login", params={"next": next_path})
    assert response.status_code == 303
    url = urlparse(response.headers["location"])
    query = parse_qs(url.query)
    return_to = query["openid.return_to"][0]
    state = parse_qs(urlparse(return_to).query)["state"][0]
    return response, return_to, state


def steam_answer(return_to, steamid=PLAYER, **override):
    params = {
        "openid.ns": steam_openid.NS, "openid.mode": "id_res", "openid.op_endpoint": steam_openid.ENDPOINT,
        "openid.claimed_id": f"https://steamcommunity.com/openid/id/{steamid}",
        "openid.identity": f"https://steamcommunity.com/openid/id/{steamid}",
        "openid.return_to": return_to, "openid.response_nonce": nonce(), "openid.assoc_handle": "1234",
        "openid.signed": "signed,op_endpoint,claimed_id,identity,return_to,response_nonce,assoc_handle",
        "openid.sig": "x",
    }
    params.update(override)
    return params


def callback(client, return_to, state, **override):
    params = steam_answer(return_to, **override)
    params["state"] = state
    return client.get("/api/auth/steam/callback", params=params)


def test_login_redirects_to_steam_with_fixed_return_address(steam):
    response, return_to, state = start(steam)
    location = response.headers["location"]
    assert location.startswith("https://steamcommunity.com/openid/login?")
    assert return_to == f"{SITE}/api/auth/steam/callback?state={state}"
    assert parse_qs(urlparse(location).query)["openid.realm"] == [SITE]
    cookie = response.headers["set-cookie"]
    assert cookie.startswith("edb_login=") and "HttpOnly" in cookie and "SameSite=lax" in cookie


def test_login_needs_a_session_secret(demo, monkeypatch):
    client = TestClient(create_app(), follow_redirects=False)
    assert client.get("/api/auth/steam/login").status_code == 503
    assert client.get("/api/me").json()["login_enabled"] is False


def test_registered_player_gets_a_session(steam):
    _, return_to, state = start(steam, "/rankings/xp")
    done = callback(steam, return_to, state)
    assert done.status_code == 303 and done.headers["location"] == "/rankings/xp"
    assert "edb_session=" in done.headers["set-cookie"]
    me = steam.get("/api/me")
    data = me.json()
    assert data["authenticated"] is True and data["is_admin"] is False
    assert data["player"]["id"] and data["player"]["name"]
    assert "steamid" not in str(data).lower().replace("login_enabled", "")
    assert me.headers["cache-control"] == "no-store"


def test_unknown_steamid_is_turned_away_without_a_session(steam):
    _, return_to, state = start(steam)
    done = callback(steam, return_to, state, steamid=STRANGER)
    assert done.headers["location"] == "/?login=desconhecido"
    assert "edb_session=" not in done.headers.get("set-cookie", "")
    assert steam.get("/api/me").json()["authenticated"] is False


@pytest.mark.parametrize("override", [
    {"openid.mode": "cancel"},
    {"openid.op_endpoint": "https://evil.example/openid/login"},
    {"openid.claimed_id": "https://steamcommunity.com.evil.example/openid/id/76561198000000101"},
    {"openid.identity": "https://steamcommunity.com/openid/id/76561198000009999"},
    {"openid.signed": "signed,return_to"},
    {"openid.response_nonce": "2001-01-01T00:00:00Zabc"},
    {"openid.return_to": "http://localhost:3000/api/auth/steam/callback?state=outro"},
])
def test_tampered_answers_are_rejected(steam, override):
    _, return_to, state = start(steam)
    done = callback(steam, return_to, state, **override)
    assert done.headers["location"] == "/?login=erro"
    assert "edb_session=" not in done.headers.get("set-cookie", "")


def test_steam_saying_invalid_is_rejected(steam, monkeypatch):
    monkeypatch.setattr(steam_openid, "check_with_steam", lambda params, timeout=6.0: False)
    _, return_to, state = start(steam)
    assert callback(steam, return_to, state).headers["location"] == "/?login=erro"


def test_state_must_match_the_cookie(steam):
    _, return_to, state = start(steam)
    forged = state[:-1] + ("0" if state[-1] != "0" else "1")
    done = steam.get("/api/auth/steam/callback", params={**steam_answer(return_to), "state": forged})
    assert done.headers["location"] == "/?login=erro"
    steam.cookies.clear()  # chegou sem passar pelo início do login
    assert callback(steam, return_to, state).headers["location"] == "/?login=erro"


def test_the_same_answer_cannot_be_replayed(steam):
    _, return_to, state = start(steam)
    params = {**steam_answer(return_to), "state": state}
    assert steam.get("/api/auth/steam/callback", params=params).headers["location"] == "/rankings/elite"
    _, again_to, again_state = start(steam)
    replay = {**params, "openid.return_to": again_to, "state": again_state}
    assert steam.get("/api/auth/steam/callback", params=replay).headers["location"] == "/?login=erro"


@pytest.mark.parametrize("bad", ["https://evil.example", "//evil.example", "/\\evil", "javascript:alert(1)", "/a b"])
def test_next_only_accepts_paths_of_the_site(steam, bad):
    _, return_to, state = start(steam, bad)
    assert callback(steam, return_to, state).headers["location"] == "/"


def test_logout_clears_the_session_and_checks_origin(steam):
    _, return_to, state = start(steam)
    callback(steam, return_to, state)
    assert steam.post("/api/auth/logout", headers={"Origin": "https://evil.example"}).status_code == 403
    assert steam.post("/api/auth/logout", headers=ORIGIN).status_code == 200
    assert steam.get("/api/me").json()["authenticated"] is False


def test_player_session_does_not_open_admin(steam):
    _, return_to, state = start(steam)
    callback(steam, return_to, state)
    assert steam.get("/api/admin/session").json()["authenticated"] is False
    assert steam.get("/api/admin/overview").status_code == 401


def test_only_the_configured_steam_account_is_admin(steam):
    _, return_to, state = start(steam, "/admin")
    done = callback(steam, return_to, state, steamid=ADMIN)
    assert done.headers["location"] == "/admin"
    me = steam.get("/api/me").json()
    assert me["authenticated"] and me["is_admin"] and me["player"] is None
    assert steam.get("/api/admin/session").json() == {"authenticated": True, "configured": True, "steam": True, "password": True}
    assert steam.get("/api/admin/overview").status_code == 200
    assert steam.post("/api/admin/players", json={"nickname": "Novo", "skill_level": 5}, headers=ORIGIN).status_code == 200
    assert steam.post("/api/admin/players", json={"nickname": "Outro", "skill_level": 5},
                      headers={"Origin": "https://evil.example"}).status_code == 403


def test_empty_password_never_opens_admin_when_only_steam_is_configured(demo, monkeypatch):
    monkeypatch.setenv("XINXAS_ADMIN_PASSWORD", "")
    monkeypatch.setenv("EDB_SESSION_SECRET", SECRET)
    monkeypatch.setenv("EDB_ADMIN_STEAMID", ADMIN)
    client = TestClient(create_app())
    assert client.get("/api/admin/session").json()["configured"] is True
    assert client.post("/api/admin/login", json={"password": ""}, headers=ORIGIN).status_code == 503
    assert client.get("/api/admin/overview").status_code == 401


def test_session_from_a_removed_player_stops_working(steam):
    _, return_to, state = start(steam)
    callback(steam, return_to, state)
    from edb_api import views

    original = views.player_for_steamid
    views.player_for_steamid = lambda snap, steamid: None
    try:
        assert steam.get("/api/me").json()["authenticated"] is False
    finally:
        views.player_for_steamid = original


def test_problems_explain_a_short_secret_without_showing_it(demo, monkeypatch, caplog):
    from edb_api import settings
    from edb_api.main import _warn_about_steam_login

    monkeypatch.setenv("EDB_SESSION_SECRET", "curto-123")
    monkeypatch.setenv("EDB_ADMIN_STEAMID", "123")
    problems = settings.steam_login_problems()
    assert any("pelo menos 16" in p and "hoje tem 9" in p for p in problems)
    assert any("SteamID64 válido" in p for p in problems)
    assert "curto-123" not in " ".join(problems)
    with caplog.at_level("WARNING", logger="edb.api"):
        _warn_about_steam_login()
    assert any("Login com a Steam" in r.message for r in caplog.records)


def test_secret_with_stray_spaces_still_counts_only_real_characters(demo, monkeypatch):
    from edb_api import settings

    monkeypatch.setenv("EDB_SESSION_SECRET", "   " + "a" * 15 + "  \n")
    assert settings.steam_login_enabled() is False
    monkeypatch.setenv("EDB_SESSION_SECRET", "\n" + "a" * 16 + " ")
    assert settings.steam_login_enabled() is True
