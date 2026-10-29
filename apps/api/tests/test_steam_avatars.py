from __future__ import annotations

from edb.steam_profile import SteamUnavailable

from .conftest import ORIGIN


def add_player(admin, nick, steamid):
    response = admin.post("/api/admin/players", json={"nickname": nick, "steamid": steamid, "skill_level": 5}, headers=ORIGIN)
    assert response.status_code == 200, response.text
    return response.json()["id"]


def test_avatars_empty_without_key(admin):
    add_player(admin, "ComFoto", "76561198000000777")
    assert admin.get("/api/steam/avatars").json() == {}


def test_avatars_use_batch_and_cache(admin, monkeypatch):
    from edb_api import service

    pid = add_player(admin, "ComFoto", "76561198000000777")
    monkeypatch.setenv("STEAM_API_KEY", "chave-de-teste")
    calls = []

    def fake(steamids, key):
        calls.append(list(steamids))
        return {"76561198000000777": "https://avatars.steamstatic.com/a.jpg"}

    monkeypatch.setattr(service, "fetch_steam_avatars", fake)
    first = admin.get("/api/steam/avatars").json()
    assert first == {pid: "https://avatars.steamstatic.com/a.jpg"}
    assert admin.get("/api/steam/avatars").json() == first
    # Uma única consulta em lote (os jogadores da demonstração também têm SteamID); a segunda visita vem do cache.
    assert len(calls) == 1 and "76561198000000777" in calls[0]


def test_avatars_survive_steam_outage(admin, monkeypatch):
    from edb_api import service

    add_player(admin, "ComFoto", "76561198000000777")
    monkeypatch.setenv("STEAM_API_KEY", "chave-de-teste")

    def down(steamids, key):
        raise SteamUnavailable("network")

    monkeypatch.setattr(service, "fetch_steam_avatars", down)
    response = admin.get("/api/steam/avatars")
    assert response.status_code == 200 and response.json() == {}
