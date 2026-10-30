"""Privacidade: o jogador esconde foto, nome na Steam e horas; o resto do site respeita na hora."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from edb_api import identity, privacy
from edb_api.main import create_app
from edb_api.service import get_service

from .conftest import ORIGIN
from .test_mvp_votes import FALCAO, NEBULOSA, SECRET, as_player
from .ts_contract import check

ALL_HIDDEN = {"hide_avatar": True, "hide_persona": True, "hide_hours": True}
NONE_HIDDEN = {"hide_avatar": False, "hide_persona": False, "hide_hours": False}


@pytest.fixture
def priv(demo, monkeypatch):
    monkeypatch.setenv("EDB_SESSION_SECRET", SECRET)
    ids = {p["nickname"]: str(p["id"]) for p in get_service().snap().players}
    return ids


def save(client, body):
    return client.post("/api/me/privacy", json=body, headers=ORIGIN)


def test_defaults_show_everything_and_need_login_to_change(priv):
    mine = as_player(FALCAO).get("/api/me/privacy").json()
    check(mine, "MyPrivacy")
    assert mine == {"available": True, **NONE_HIDDEN}
    assert as_player(None).get("/api/me/privacy").json()["available"] is False
    assert save(as_player(None), ALL_HIDDEN).status_code == 401


def test_saved_choices_are_returned_and_isolated_per_player(priv):
    me = as_player(FALCAO)
    assert save(me, {**NONE_HIDDEN, "hide_hours": True}).json() == {"available": True, **NONE_HIDDEN, "hide_hours": True}
    assert as_player(FALCAO).get("/api/me/privacy").json()["hide_hours"] is True
    assert as_player(NEBULOSA).get("/api/me/privacy").json()["hide_hours"] is False


def test_hidden_items_disappear_from_the_public_profile(priv, monkeypatch):
    view = {"state": "linked", "avatar": "https://x/a.jpg", "persona": "Fulano", "hours": 1234.5, "note": ""}
    monkeypatch.setattr("edb_api.views.steam_view", lambda *a, **k: dict(view))
    public = TestClient(create_app())
    pid = priv["Falcão"]
    assert public.get(f"/api/players/{pid}").json()["steam"] == view
    save(as_player(FALCAO), {"hide_avatar": True, "hide_persona": True, "hide_hours": False})
    shown = public.get(f"/api/players/{pid}")
    # a rota pública tem cache curto de borda, mas o servidor recalcula a cada chamada
    steam = shown.json()["steam"]
    assert steam["avatar"] == "" and steam["persona"] == "" and steam["hours"] == 1234.5
    other = public.get(f"/api/players/{priv['Nebulosa']}").json()["steam"]
    assert other == view


def test_hidden_avatar_leaves_the_avatars_list(priv, monkeypatch):
    monkeypatch.setenv("STEAM_API_KEY", "chave")
    service = get_service()
    monkeypatch.setattr(service, "steam_avatars", lambda ids, key: {i: f"https://x/{i}.jpg" for i in ids})
    public = TestClient(create_app())
    assert priv["Falcão"] in public.get("/api/steam/avatars").json()
    save(as_player(FALCAO), ALL_HIDDEN)
    assert priv["Falcão"] not in public.get("/api/steam/avatars").json()


def test_unavailable_without_table_and_never_exposes_steamid(priv, monkeypatch):
    service = get_service()
    original = service.store._api

    def missing(method, table, **kw):
        if table == privacy.TABLE:
            raise RuntimeError("relation does not exist")
        return original(method, table, **kw)

    monkeypatch.setattr(service.store, "_api", missing)
    assert as_player(FALCAO).get("/api/me/privacy").json()["available"] is False
    assert save(as_player(FALCAO), ALL_HIDDEN).status_code == 400
    assert FALCAO not in as_player(FALCAO).get(f"/api/players/{priv['Falcão']}").text


def test_privacy_post_checks_origin(priv):
    response = as_player(FALCAO).post("/api/me/privacy", json=ALL_HIDDEN, headers={"Origin": "https://outro.example"})
    assert response.status_code == 403
