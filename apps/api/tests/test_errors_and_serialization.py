from __future__ import annotations

import math
from datetime import date

import numpy as np
import pandas as pd

from edb_api.serializers import clean


def test_clean_converts_numpy_nan_and_dates():
    frame = pd.DataFrame({"a": [1, np.nan], "b": [np.int64(3), np.int64(4)], "d": pd.to_datetime(["2026-10-19", None])})
    out = clean({"rows": frame, "x": np.float64("nan"), "inf": float("inf"), "ok": np.bool_(True),
                 "day": date(2026, 10, 19), "set": {"b", "a"}, "ts": pd.Timestamp("2026-10-19 13:30")})
    assert out["rows"][1]["a"] is None and out["rows"][1]["d"] is None
    assert out["rows"][0]["d"] == "2026-10-19" and out["rows"][0]["b"] == 3
    assert out["x"] is None and out["inf"] is None and out["ok"] is True
    assert out["day"] == "2026-10-19" and out["set"] == ["a", "b"] and out["ts"] == "2026-10-19T13:30:00"
    assert not any(isinstance(v, float) and math.isnan(v) for v in out["rows"][0].values())


def test_not_found_and_bad_requests(client):
    assert client.get("/api/players/inexistente").status_code == 404
    assert client.get("/api/players/inexistente").json()["detail"] == "Jogador não encontrado."
    assert client.get("/api/matches/inexistente").status_code == 404
    assert client.get("/api/rankings/inexistente").status_code == 404
    assert client.get("/api/rota-que-nao-existe").json()["detail"] == "Rota não encontrada."
    players = [p["id"] for p in client.get("/api/players").json()]
    same = client.get(f"/api/compare?a={players[0]}&b={players[0]}")
    assert same.status_code == 400 and "dois jogadores diferentes" in same.json()["detail"]
    assert client.get(f"/api/compare?a={players[0]}&b=inexistente").status_code == 404
    assert client.get("/api/compare?a=x").status_code == 422


def test_draw_validation(client):
    players = [p["id"] for p in client.get("/api/players").json()]
    assert client.post("/api/draw", json={"player_ids": players[:9]}).status_code == 400
    assert client.post("/api/draw", json={"player_ids": players[:9] + [players[0]]}).status_code == 400
    assert client.post("/api/draw", json={"player_ids": players[:9] + ["nao-existe"]}).status_code == 404
    everyone = [p["id"] for p in client.get("/api/players?include_inactive=true").json()]
    inactive = [p["id"] for p in client.get("/api/players?include_inactive=true").json() if not p["is_active"]][0]
    assert client.post("/api/draw", json={"player_ids": players[:9] + [inactive]}).status_code == 404
    assert client.post("/api/draw", json={}).status_code == 422
    assert everyone


def test_boards_match_direct_calculation(client, demo):
    from edb.core import enrich
    from edb.season_rankings import season_boards
    snap = demo.snap()
    frame = enrich(snap.players, snap.matches, snap.stats)
    selected = frame[frame["match_id"].astype(str).isin(snap.season_ids(1))]
    stars = {str(r["player_id"]): int(r["stars"]) for r in snap.frozen_stars if int(r["season_number"]) == 1}
    direct = season_boards(selected, 1, stars)
    for rtype, column in (("elite", "Elite"), ("superacao", "Superação %"), ("xp", "XP")):
        rows = client.get(f"/api/rankings/{rtype}").json()["rows"]
        expected = direct[rtype]
        assert [r["player_id"] for r in rows] == list(expected["player_id"])
        assert [r["focus"] for r in rows] == [float(x) for x in expected[column]]
        assert [r["eligible"] for r in rows] == [bool(x) for x in expected["Elegível"]]
        assert [r["provisional"] for r in rows] == [not bool(x) for x in expected["Elegível"]]


def test_provisional_players_are_flagged(client):
    rows = client.get("/api/rankings/elite").json()["rows"]
    provisional = {r["name"] for r in rows if r["provisional"]}
    assert provisional == {"Rafael (Falcão)", "Davi (Tubarão)", "Orca", "Pantera"}
    assert all(r["eligible"] for r in rows[:10])


def test_highlights_only_use_eligible_players(client):
    home = client.get("/api/home").json()
    rows = {r["player_id"]: r for r in client.get("/api/rankings/elite").json()["rows"]}
    for item in home["highlights"]:
        assert item["player"] is not None
        assert rows[item["player"]["id"]]["eligible"] is True


def test_empty_local_database_returns_valid_empty_data(local_client):
    for path in ("/api/home", "/api/rankings/elite", "/api/rankings/bagres", "/api/matches",
                 "/api/hall-of-fame", "/api/medals", "/api/players", "/api/missions"):
        response = local_client.get(path)
        assert response.status_code == 200, (path, response.text)
    home = local_client.get("/api/home").json()
    assert [h["player"] for h in home["highlights"]] == [None, None, None]
    assert home["highlights"][0]["detail"] == "Exige pelo menos 6 mapas"
    meta = local_client.get("/api/meta").json()
    assert meta["demo"] is False and meta["cloud"] is False and len(meta["seasons"]) == 1
