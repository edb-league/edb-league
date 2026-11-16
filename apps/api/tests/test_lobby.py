"""Lobby do servidor: entrar nos times, capitão = primeiro de cada time, JSON do MatchZy com 10/10."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from edb_api import identity
from edb_api.main import create_app

from .conftest import ORIGIN, PASSWORD

SECRET = "segredo-de-teste-com-mais-de-16-caracteres"
STEAMS = [f"7656119800000{i:04d}" for i in range(1, 13)]


@pytest.fixture
def lobby(local, monkeypatch):
    monkeypatch.setenv("EDB_SESSION_SECRET", SECRET)
    for index, steam in enumerate(STEAMS):
        local.store.save_player(f"Jogador{index + 1}", steamid=steam)
    return local


def as_player(index: int) -> TestClient:
    client = TestClient(create_app())
    client.cookies.set(identity.SESSION_COOKIE, identity._pack("session", STEAMS[index], 3600))
    return client


def act(client, method, path, **kwargs):
    return client.request(method, "/api/lobby" + path, headers=ORIGIN, **kwargs)


def fill(count_per_team=5):
    for i in range(count_per_team):
        assert act(as_player(i), "POST", "/join", json={"team": 1}).status_code == 200
        assert act(as_player(i + 5), "POST", "/join", json={"team": 2}).status_code == 200


def test_empty_lobby_is_public_and_hides_steamids(lobby):
    view = TestClient(create_app()).get("/api/lobby")
    assert view.status_code == 200 and view.headers["cache-control"] == "no-store"
    data = view.json()
    assert data["count"] == 0 and not data["ready"] and data["map"] == "de_mirage" and data["format"] == "md1"
    assert data["me"]["team"] is None and not data["me"]["can_configure"]
    assert "7656119" not in view.text


def test_first_to_join_is_captain_and_leaving_promotes_the_next(lobby):
    for i in (0, 1, 2):
        act(as_player(i), "POST", "/join", json={"team": 1})
    team = act(as_player(0), "GET", "").json()["teams"][0]["players"]
    assert [p["captain"] for p in team] == [True, False, False]
    assert [p["name"] for p in team] == ["Jogador1", "Jogador2", "Jogador3"]
    left = act(as_player(0), "POST", "/leave")
    assert left.status_code == 200
    team = left.json()["teams"][0]["players"]
    assert team[0]["name"] == "Jogador2" and team[0]["captain"] is True


def test_join_rules(lobby):
    anonymous = TestClient(create_app())
    assert act(anonymous, "POST", "/join", json={"team": 1}).status_code == 401
    stranger = TestClient(create_app())
    stranger.cookies.set(identity.SESSION_COOKIE, identity._pack("session", "76561198000099999", 3600))
    assert act(stranger, "POST", "/join", json={"team": 1}).status_code == 403
    assert act(as_player(0), "POST", "/join", json={"team": 3}).status_code == 400
    assert act(as_player(0), "POST", "/join", json={"team": 1}).status_code == 200
    assert act(as_player(0), "POST", "/join", json={"team": 2}).status_code == 409  # já está no lobby
    assert act(as_player(1), "POST", "/leave").status_code == 404
    foreign = {"Origin": "https://outro-site.example"}
    assert as_player(1).post("/api/lobby/join", headers=foreign, json={"team": 1}).status_code == 403


def test_team_is_limited_to_five(lobby):
    for i in range(5):
        act(as_player(i), "POST", "/join", json={"team": 1})
    assert act(as_player(5), "POST", "/join", json={"team": 1}).status_code == 409


def test_only_captains_or_admin_configure(lobby):
    act(as_player(0), "POST", "/join", json={"team": 1})
    act(as_player(1), "POST", "/join", json={"team": 1})
    act(as_player(2), "POST", "/join", json={"team": 2})
    assert act(as_player(1), "PATCH", "", json={"map": "de_nuke"}).status_code == 403
    assert act(as_player(3), "PATCH", "", json={"map": "de_nuke"}).status_code == 403
    done = act(as_player(0), "PATCH", "", json={"map": "de_nuke", "format": "md3"})
    assert done.status_code == 200 and done.json()["map"] == "de_nuke" and done.json()["format"] == "md3"
    assert act(as_player(2), "PATCH", "", json={"format": "md5"}).json()["format"] == "md5"  # capitão do time 2
    assert act(as_player(0), "PATCH", "", json={"map": "de_xyz"}).status_code == 400
    assert act(as_player(0), "PATCH", "", json={"format": "md9"}).status_code == 400


def test_matchzy_json_needs_ten_players_and_membership(lobby):
    fill(4)
    assert act(as_player(0), "GET", "/matchzy").status_code == 409
    act(as_player(4), "POST", "/join", json={"team": 1})
    assert act(as_player(0), "GET", "/matchzy").status_code == 409  # time 2 ainda com 4
    act(as_player(9), "POST", "/join", json={"team": 2})
    assert act(as_player(0), "PATCH", "", json={"format": "md3", "map": "de_inferno"}).status_code == 200
    assert act(as_player(10), "GET", "/matchzy").status_code == 403  # fora do lobby
    assert act(TestClient(create_app()), "GET", "/matchzy").status_code == 401
    body = act(as_player(0), "GET", "/matchzy").json()
    config = body["config"]
    assert config["num_maps"] == 3 and config["skip_veto"] is False and config["maplist"][0] == "de_inferno"
    assert len(set(config["maplist"])) == len(config["maplist"]) == 7
    assert list(config["team1"]["players"]) == STEAMS[:5] and list(config["team2"]["players"]) == STEAMS[5:10]
    assert config["players_per_team"] == 5 and body["json"].startswith("{")


def test_md1_skips_veto_with_single_map(lobby):
    fill()
    config = act(as_player(0), "GET", "/matchzy").json()["config"]
    assert config["num_maps"] == 1 and config["skip_veto"] is True and config["maplist"] == ["de_mirage"]
    assert act(as_player(0), "GET", "").json()["ready"] is True


def test_admin_can_remove_and_reset(lobby):
    fill(2)
    anonymous = TestClient(create_app())
    assert act(anonymous, "DELETE", "").status_code in (401, 503)
    admin = TestClient(create_app())
    assert admin.post("/api/admin/login", json={"password": PASSWORD}, headers=ORIGIN).status_code == 200
    removed = act(admin, "DELETE", "/players/" + act(admin, "GET", "").json()["teams"][0]["players"][1]["id"])
    assert removed.status_code == 200 and removed.json()["count"] == 3
    assert act(admin, "PATCH", "", json={"map": "de_ancient"}).json()["map"] == "de_ancient"
    assert act(admin, "DELETE", "").json()["count"] == 0


def test_spectators_join_limit_and_go_into_matchzy_json(lobby):
    fill()
    for i in (10, 11):
        assert act(as_player(i), "POST", "/join", json={"team": 0}).status_code == 200
    view = act(as_player(10), "GET", "").json()
    assert [p["name"] for p in view["spectators"]["players"]] == ["Jogador11", "Jogador12"]
    assert view["spectators"]["slots"] == 5 and view["me"]["team"] == 0 and view["count"] == 10
    assert act(as_player(10), "GET", "/matchzy").status_code == 200  # espectador também recebe o JSON
    config = act(as_player(0), "GET", "/matchzy").json()["config"]
    assert list(config["spectators"]["players"]) == STEAMS[10:12]
    assert act(as_player(10), "POST", "/leave").status_code == 200


def test_connect_only_for_people_in_the_lobby(lobby, monkeypatch):
    monkeypatch.setenv("SERVER_CONNECT", "1.2.3.4:27015")
    monkeypatch.setenv("SERVER_PASSWORD", "segredo")
    outsider = as_player(11)
    assert outsider.get("/api/lobby").json()["me"]["connect"] == ""
    assert TestClient(create_app()).get("/api/lobby").json()["me"]["connect"] == ""
    member = as_player(0)
    act(member, "POST", "/join", json={"team": 1})
    assert member.get("/api/lobby").json()["me"]["connect"] == "password segredo; connect 1.2.3.4:27015"
    assert member.get("/api/lobby").json()["me"]["address"] == "1.2.3.4:27015"
    assert outsider.get("/api/lobby").json()["me"]["address"] == ""
    monkeypatch.delenv("SERVER_PASSWORD")
    assert member.get("/api/lobby").json()["me"]["connect"] == "connect 1.2.3.4:27015"
    monkeypatch.delenv("SERVER_CONNECT")
    assert member.get("/api/lobby").json()["me"]["connect"] == ""
