from __future__ import annotations

import pytest

from edb_api import identity, skins_ops
from .conftest import ORIGIN

STEAMID = "76561198000000001"


class FakeDB:
    """Imita só o que o skins_ops usa: skins e facas por (steamid, time, arma)."""

    def __init__(self):
        self.skins: dict = {}
        self.knives: dict = {}
        self.last = None

    def cursor(self):
        return self

    def execute(self, sql, params=()):
        s = " ".join(sql.split())
        if s.startswith("INSERT INTO wp_player_skins"):
            steam, team, weapon, paint, wear, seed = params
            self.skins[(steam, team, weapon)] = (paint, wear, seed)
        elif s.startswith("INSERT INTO wp_player_knife"):
            steam, team, knife = params
            self.knives[(steam, team)] = knife
        elif s.startswith("DELETE FROM wp_player_skins"):
            steam, weapon = params
            self.skins = {k: v for k, v in self.skins.items() if not (k[0] == steam and k[2] == weapon)}
        elif s.startswith("DELETE FROM wp_player_knife"):
            steam, knife = params
            self.knives = {k: v for k, v in self.knives.items() if not (k[0] == steam and v == knife)}
        elif s.startswith("SELECT weapon_defindex"):
            self.last = [(k[2], *v) for k, v in self.skins.items() if k[0] == params[0] and k[1] == 2]
        elif s.startswith("SELECT knife"):
            knife = self.knives.get((params[0], 2))
            self.last = [(knife,)] if knife else []
        else:
            raise AssertionError(sql)

    def fetchall(self):
        return self.last

    def fetchone(self):
        return self.last[0] if self.last else None

    def commit(self): ...
    def rollback(self): ...
    def close(self): ...


@pytest.fixture
def wp(monkeypatch):
    db = FakeDB()
    monkeypatch.setenv("WP_DB_HOST", "127.0.0.1")
    monkeypatch.setattr(skins_ops, "_connect", lambda: db)
    monkeypatch.setattr(skins_ops, "_pairs", lambda: {(7, 490), (507, 413)})
    return db


@pytest.fixture
def logged(client, monkeypatch):
    monkeypatch.setenv("EDB_SESSION_SECRET", "x" * 40)
    monkeypatch.setenv("EDB_PUBLIC_URL", "http://localhost:3000")
    client.cookies.set("edb_session", identity._pack("session", STEAMID, 3600))
    return client


def test_disabled_without_database(client):
    data = client.get("/api/skins/me").json()
    assert data["enabled"] is False and data["equipped"] == []


def test_requires_login(client, wp):
    assert client.get("/api/skins/me").json()["authenticated"] is False
    response = client.post("/api/skins/equip", json={"weapon_id": 7, "paint_id": 490}, headers=ORIGIN)
    assert response.status_code == 401


def test_equip_writes_both_teams(logged, wp):
    response = logged.post("/api/skins/equip", json={"weapon_id": 7, "paint_id": 490, "wear": 0.5, "seed": 12}, headers=ORIGIN)
    assert response.status_code == 200, response.text
    assert {k[1] for k in wp.skins} == {2, 3}
    assert response.json()["equipped"] == [{"weapon_id": 7, "paint_id": 490, "wear": 0.5, "seed": 12}]
    assert logged.get("/api/skins/me").headers["cache-control"] == "no-store"


def test_equip_clamps_and_rejects_unknown(logged, wp):
    logged.post("/api/skins/equip", json={"weapon_id": 7, "paint_id": 490, "wear": 9, "seed": 99999}, headers=ORIGIN)
    assert wp.skins[(STEAMID, 2, 7)] == (490, 1.0, 1000)
    assert logged.post("/api/skins/equip", json={"weapon_id": 7, "paint_id": 1}, headers=ORIGIN).status_code == 400


def test_knife_sets_model_and_unequip(logged, wp):
    data = logged.post("/api/skins/equip", json={"weapon_id": 507, "paint_id": 413}, headers=ORIGIN).json()
    assert data["knife"] == "weapon_knife_karambit"
    data = logged.delete("/api/skins/equip/507", headers=ORIGIN).json()
    assert data["equipped"] == [] and data["knife"] is None


def test_write_blocked_from_other_origin(logged, wp):
    response = logged.post("/api/skins/equip", json={"weapon_id": 7, "paint_id": 490}, headers={"Origin": "http://evil.example"})
    assert response.status_code == 403


# ---- modo ponte: a API guarda na tabela skin_selections e o script do servidor busca as mudanças ----

TOKEN = "token-da-ponte-de-teste"


@pytest.fixture
def bridge(local, monkeypatch):
    from fastapi.testclient import TestClient

    from edb_api.main import create_app

    monkeypatch.setenv("BRIDGE_TOKEN", TOKEN)
    monkeypatch.setenv("EDB_SESSION_SECRET", "x" * 40)
    monkeypatch.setenv("EDB_PUBLIC_URL", "http://localhost:3000")
    monkeypatch.setattr(skins_ops, "_pairs", lambda: {(7, 490), (9, 344), (507, 413), (500, 12)})
    client = TestClient(create_app())
    client.cookies.set("edb_session", identity._pack("session", STEAMID, 3600))
    return client


AUTH = {"Authorization": f"Bearer {TOKEN}"}


def test_bridge_equip_and_view(bridge):
    assert bridge.get("/api/skins/me").json()["enabled"] is True
    data = bridge.post("/api/skins/equip", json={"weapon_id": 7, "paint_id": 490, "wear": 0.3, "seed": 5}, headers=ORIGIN).json()
    assert data["equipped"] == [{"weapon_id": 7, "paint_id": 490, "wear": pytest.approx(0.3), "seed": 5}]
    data = bridge.delete("/api/skins/equip/7", headers=ORIGIN).json()
    assert data["equipped"] == []


def test_bridge_knife_is_latest(bridge):
    bridge.post("/api/skins/equip", json={"weapon_id": 507, "paint_id": 413}, headers=ORIGIN)
    data = bridge.post("/api/skins/equip", json={"weapon_id": 500, "paint_id": 12}, headers=ORIGIN).json()
    assert data["knife"] == "weapon_bayonet"
    assert bridge.delete("/api/skins/equip/500", headers=ORIGIN).json()["knife"] == "weapon_knife_karambit"


def test_bridge_changes_requires_token(bridge):
    assert bridge.get("/api/skins/bridge/changes").status_code == 401
    assert bridge.get("/api/skins/bridge/changes", headers={"Authorization": "Bearer errado"}).status_code == 401


def test_bridge_changes_disabled_without_token(local):
    from fastapi.testclient import TestClient

    from edb_api.main import create_app

    assert TestClient(create_app()).get("/api/skins/bridge/changes", headers=AUTH).status_code == 503


def test_bridge_changes_cursor_and_removals(bridge):
    bridge.post("/api/skins/equip", json={"weapon_id": 7, "paint_id": 490}, headers=ORIGIN)
    first = bridge.get("/api/skins/bridge/changes", headers=AUTH)
    assert first.headers["cache-control"] == "no-store"
    body = first.json()
    assert [(c["steamid"], c["weapon_id"], c["deleted"]) for c in body["changes"]] == [(STEAMID, 7, False)]
    cursor = body["cursor"]
    assert bridge.get("/api/skins/bridge/changes", params={"since": cursor}, headers=AUTH).json()["changes"] == []
    bridge.post("/api/skins/equip", json={"weapon_id": 9, "paint_id": 344}, headers=ORIGIN)
    bridge.delete("/api/skins/equip/7", headers=ORIGIN)
    later = bridge.get("/api/skins/bridge/changes", params={"since": cursor}, headers=AUTH).json()["changes"]
    assert [(c["weapon_id"], c["deleted"]) for c in later] == [(9, False), (7, True)]
    assert bridge.get("/api/skins/bridge/changes", params={"since": "ontem"}, headers=AUTH).status_code == 400


def test_apply_change_writes_both_teams():
    from edb import weaponpaints

    db = FakeDB()
    weaponpaints.apply_change(db, {"steamid": STEAMID, "weapon_id": 507, "paint_id": 413, "wear": 0.2, "seed": 3, "deleted": False})
    assert {k[1] for k in db.skins} == {2, 3} and db.knives[(STEAMID, 2)] == "weapon_knife_karambit"
    weaponpaints.apply_change(db, {"steamid": STEAMID, "weapon_id": 507, "paint_id": 0, "deleted": True})
    assert db.skins == {} and db.knives == {}
