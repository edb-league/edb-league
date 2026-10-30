"""Votação de MVP da partida: quem pode votar, troca de voto, fechamento e privacidade."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from edb_api import identity, mvp
from edb_api.main import create_app
from edb_api.service import get_service

from .conftest import ORIGIN
from .ts_contract import check

SECRET = "segredo-de-teste-com-mais-de-16-caracteres"
FALCAO, NEBULOSA, FAISCA = "76561198000000101", "76561198000000104", "76561198000000108"
OUTSIDER = "76561198000000199"


@pytest.fixture
def votes(demo, monkeypatch):
    monkeypatch.setenv("EDB_SESSION_SECRET", SECRET)
    monkeypatch.setattr(mvp, "VOTE_DAYS", 100000)   # a partida da demonstração é antiga: mantém a votação aberta
    snap = get_service().snap()
    match_id = str(snap.matches[0]["id"])
    ids = {p["nickname"]: str(p["id"]) for p in snap.players}
    return match_id, ids


def as_player(steamid):
    client = TestClient(create_app())
    if steamid:
        client.cookies.set("edb_session", identity._pack("session", steamid, 3600))
    return client


def state(client, match_id):
    response = client.get(f"/api/votes/mvp/{match_id}")
    assert response.status_code == 200, response.text
    return response.json()


def vote(client, match_id, candidate):
    return client.post(f"/api/votes/mvp/{match_id}", json={"player_id": candidate}, headers=ORIGIN)


def test_anonymous_sees_open_vote_without_results(votes):
    match_id, _ = votes
    data = state(as_player(None), match_id)
    check(data, "MatchMvp")
    assert data["status"] == "open" and data["electorate"] == 10 and data["results"] is None
    assert data["viewer"]["can_vote"] is False and "Steam" in data["viewer"]["reason"]


def test_never_cached(votes):
    match_id, _ = votes
    assert as_player(None).get(f"/api/votes/mvp/{match_id}").headers["cache-control"] == "no-store"


def test_participant_votes_changes_vote_and_cannot_vote_for_self(votes):
    match_id, ids = votes
    me = as_player(FALCAO)
    assert state(me, match_id)["viewer"]["can_vote"] is True
    assert all(c["id"] != ids["Falcão"] for c in state(me, match_id)["candidates"])
    assert vote(me, match_id, ids["Falcão"]).status_code == 400
    first = vote(me, match_id, ids["Lince"])
    assert first.status_code == 200 and first.json()["viewer"]["my_vote"] == ids["Lince"]
    second = vote(me, match_id, ids["Cobra"])
    assert second.json()["viewer"]["my_vote"] == ids["Cobra"] and second.json()["votes_cast"] == 1


def test_results_stay_hidden_while_open_and_voters_are_never_exposed(votes):
    match_id, ids = votes
    vote(as_player(FALCAO), match_id, ids["Lince"])
    vote(as_player(NEBULOSA), match_id, ids["Lince"])
    data = state(as_player(FAISCA), match_id)
    assert data["status"] == "open" and data["results"] is None and data["votes_cast"] == 2
    assert FALCAO not in str(data) and "voter" not in str(data)


def test_outsiders_strangers_and_foreign_candidates_are_refused(votes):
    match_id, ids = votes
    assert vote(as_player(None), match_id, ids["Lince"]).status_code == 401
    assert vote(as_player(OUTSIDER), match_id, ids["Lince"]).status_code == 403
    assert vote(as_player(FALCAO), match_id, "nao-existe").status_code == 400
    assert vote(as_player(FALCAO), "partida-que-nao-existe", ids["Lince"]).status_code == 404


def test_vote_requires_allowed_origin(votes):
    match_id, ids = votes
    me = as_player(FALCAO)
    response = me.post(f"/api/votes/mvp/{match_id}", json={"player_id": ids["Lince"]},
                       headers={"Origin": "https://outro-site.example"})
    assert response.status_code == 403


def test_closes_when_window_ends_and_shows_winner_and_ties(votes, monkeypatch):
    match_id, ids = votes
    vote(as_player(FALCAO), match_id, ids["Lince"])
    vote(as_player(NEBULOSA), match_id, ids["Cobra"])
    vote(as_player(FAISCA), match_id, ids["Lince"])
    monkeypatch.setattr(mvp, "VOTE_DAYS", 1)           # a janela passa a estar vencida
    data = state(as_player(FALCAO), match_id)
    assert data["status"] == "closed" and data["viewer"]["can_vote"] is False
    assert [(r["player"]["id"], r["votes"], r["mvp"]) for r in data["results"]] == [
        (ids["Lince"], 2, True), (ids["Cobra"], 1, False)]
    assert vote(as_player(FALCAO), match_id, ids["Cobra"]).status_code == 409


def test_tie_marks_every_leader(votes, monkeypatch):
    match_id, ids = votes
    vote(as_player(FALCAO), match_id, ids["Lince"])
    vote(as_player(NEBULOSA), match_id, ids["Cobra"])
    monkeypatch.setattr(mvp, "VOTE_DAYS", 1)
    assert [r["mvp"] for r in state(as_player(None), match_id)["results"]] == [True, True]


def test_unavailable_when_the_table_does_not_exist_yet(votes, monkeypatch):
    match_id, _ = votes
    service = get_service()
    original = service.store._api

    def missing(method, table, **kw):
        if table == mvp.TABLE:
            raise RuntimeError("relation does not exist")
        return original(method, table, **kw)

    monkeypatch.setattr(service.store, "_api", missing)
    data = state(as_player(FALCAO), match_id)
    check(data, "MatchMvp")
    assert data["status"] == "unavailable"
    assert vote(as_player(FALCAO), match_id, "x").status_code == 400
