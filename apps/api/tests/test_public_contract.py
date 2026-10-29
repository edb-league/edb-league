"""Cada rota pública confere com os tipos de apps/web/src/lib/types.ts."""
from __future__ import annotations

import json

import pytest

from .ts_contract import check


def strict_json(text: str):
    def refuse(token):
        raise AssertionError("JSON com valor não finito: " + token)
    return json.loads(text, parse_constant=refuse)


def get(client, path):
    response = client.get(path)
    assert response.status_code == 200, f"{path}: {response.status_code} {response.text[:300]}"
    return strict_json(response.text)


def test_health(client):
    assert get(client, "/api/health") == {"ok": True}


def test_meta(client):
    data = get(client, "/api/meta")
    check(data, "Meta")
    assert data["demo"] is True
    assert data["current_season"] == 1
    assert [s["number"] for s in data["seasons"]] == [0, 1, 2]
    season = next(s for s in data["seasons"] if s["number"] == 1)
    assert season["status"] == "active" and season["progress"]["total_days"] == 31
    assert season["completed_series"] == 5


def test_home(client):
    data = get(client, "/api/home")
    check(data, "Home")
    assert [h["title"] for h in data["highlights"]] == ["MVP", "Revelação", "Xinxa"]
    assert len(data["roster"]) == 12
    assert len(data["top_elite"]) == 10
    assert data["counts"]["matches"] == 10


@pytest.mark.parametrize("rtype", ["elite", "superacao", "xp", "bagres"])
def test_rankings(client, rtype):
    data = get(client, f"/api/rankings/{rtype}")
    check(data, "Ranking")
    assert data["type"] == rtype
    assert [r["rank"] for r in data["rows"]] == list(range(1, len(data["rows"]) + 1))
    if rtype == "superacao":
        assert isinstance(data["progress"], list)
    else:
        assert data["progress"] is None
    if rtype == "bagres":
        assert all(r["stars"] == 0 and r["elite"] is None for r in data["rows"])
        adr = [r["adr"] for r in data["rows"]]
        assert adr == sorted(adr)


def test_ranking_season_zero_uses_homologated_snapshot(client):
    data = get(client, "/api/rankings/elite?season=0")
    check(data, "Ranking")
    assert data["season"]["number"] == 0 and data["season"]["homologated"] is True
    assert len(data["rows"]) > 0


def test_unknown_season_falls_back_to_current(client):
    assert get(client, "/api/rankings/xp?season=99")["season"]["number"] == 1
    assert get(client, "/api/rankings/xp?season=abc")["season"]["number"] == 1


def test_missions(client):
    data = get(client, "/api/missions")
    check(data, "Missions")
    assert [t["stars"] for t in data["targets"]] == [1, 2, 3, 4, 5]


def test_players_list(client):
    active = get(client, "/api/players")
    check(active, "PlayerListItem", array=True)
    assert len(active) == 12 and all(p["is_active"] for p in active)
    everyone = get(client, "/api/players?include_inactive=true")
    assert len(everyone) == 14
    assert not any("steamid" in p for p in everyone)


def test_player_detail(client):
    players = get(client, "/api/players")
    first = players[0]["id"]
    data = get(client, f"/api/players/{first}")
    check(data, "PlayerDetail")
    assert data["summary"]["games"] == len(data["matches"])
    dates = [m["date"] for m in data["matches"]]
    assert dates == sorted(dates, reverse=True)
    assert len(data["medals"]) == 15
    assert data["steam"]["state"] in {"unlinked", "no_key"}


def test_inactive_player_detail_still_opens(client):
    everyone = get(client, "/api/players?include_inactive=true")
    inactive = next(p for p in everyone if not p["is_active"])
    check(get(client, f"/api/players/{inactive['id']}"), "PlayerDetail")


def test_compare(client):
    players = get(client, "/api/players")
    a, b = players[0]["id"], players[1]["id"]
    data = get(client, f"/api/compare?a={a}&b={b}")
    check(data, "Compare")
    assert data["shared_count"] == len(data["shared"])
    assert data["opponent_games"] + data["teammate_games"] <= data["shared_count"]


def test_hall_of_fame(client):
    data = get(client, "/api/hall-of-fame")
    check(data, "Hall")
    assert data["match_count"] == 18
    assert data["henio"] is not None and len(data["top_kills"]) == 5
    assert {t["title"] for t in data["titles"]} == {"MVP", "Revelação", "Xinxa"}


def test_medals(client):
    data = get(client, "/api/medals")
    check(data, "MedalCatalogue")
    assert data["summary"]["available"] == len(data["medals"]) == 15


def test_matches_list(client):
    data = get(client, "/api/matches")
    check(data, "MatchesList")
    assert len(data["bo1"]) == 3 and len(data["bo3"]) == 4
    statuses = {s["status"] for s in data["bo3"]}
    assert statuses == {"FINALIZADA", "EM ANDAMENTO", "AGUARDANDO REGISTRO"}
    # PT fica sempre à esquerda, mesmo quando o registro guardou PL como time A.
    assert all(s["left"] == "PT" and s["right"] == "PL" for s in data["bo1"] + data["bo3"])
    swapped = next(s for s in data["bo1"] if s["id"] == "ser-t1-03")
    assert (swapped["score_left"], swapped["score_right"], swapped["winner"]) == (13, 9, "left")
    assert len(data["legacy"]) == 2


def test_match_detail(client):
    listing = get(client, "/api/matches")
    series = next(s for s in listing["bo3"] if s["id"] == "ser-t1-01")
    data = get(client, f"/api/matches/{series['maps'][0]['id']}")
    check(data, "MatchDetail")
    assert data["series_id"] == "ser-t1-01" and data["series_format"] == "bo3" and data["season"] == 1
    assert {t["outcome"] for t in data["teams"]} == {"win", "loss"}
    assert data["aim"] and data["utility"]
    assert data["coverage"]["players"] == 10


def test_match_detail_legacy_and_without_scope(client):
    listing = get(client, "/api/matches")
    legacy_id = listing["legacy"][0]["id"]
    data = get(client, f"/api/matches/{legacy_id}")
    check(data, "MatchDetail")
    assert data["series_id"] is None and data["aim"] == [] and data["utility"] == []


def test_draw(client):
    ids = [p["id"] for p in get(client, "/api/players")][:10]
    response = client.post("/api/draw", json={"player_ids": ids})
    assert response.status_code == 200
    data = strict_json(response.text)
    check(data, "DrawResult")
    assert len(data["team_a"]) == len(data["team_b"]) == 5
    assert {p["id"] for p in data["team_a"] + data["team_b"]} == set(ids)
    assert data["gap"] == abs(data["total_a"] - data["total_b"])
    assert "SORTEIO DE TIMES" in data["message"]


def test_cache_headers(client):
    assert "s-maxage" in client.get("/api/home").headers["cache-control"]
    assert client.get("/api/admin/session").headers["cache-control"] == "no-store"
    ids = [p["id"] for p in client.get("/api/players").json()][:10]
    assert client.post("/api/draw", json={"player_ids": ids}).headers["cache-control"] == "no-store"


def test_perfil_avancado_aparece_so_com_demo(client, demo):
    """Jogadores com partidas analisadas por demo recebem o bloco `advanced`; os demais, null."""
    players = get(client, "/api/players")
    items = players if isinstance(players, list) else players["players"]
    details = [get(client, f"/api/players/{p['id']}") for p in items]
    with_demo = [d for d in details if d["advanced"] is not None]
    assert with_demo, "a demonstração deveria ter jogadores com demo"
    sample = with_demo[0]["advanced"]
    assert sample["coverage"]["maps_with_demo"] <= sample["coverage"]["maps_total"]
    assert {s["key"] for s in sample["scores"]} == {"firepower", "entrying", "trading", "opening", "closing", "sniping", "utility"}
    assert all(0 <= s["value"] <= 100 for s in sample["scores"] if s["value"] is not None)


def _first_with_demo(client):
    players = get(client, "/api/players")
    items = players if isinstance(players, list) else players["players"]
    for p in items:
        detail = get(client, f"/api/players/{p['id']}")
        if detail["advanced"] is not None:
            return p["id"], detail
    raise AssertionError("a demonstração deveria ter jogador com demo")


def test_perfil_avancado_filtros(client, demo):
    pid, base = _first_with_demo(client)
    check(base, "PlayerDetail")
    assert base["headline"]["rating2"] is not None
    options = base["advanced"]["filters"]["options"]
    assert options["maps"] and options["formats"] and options["seasons"]
    assert base["advanced"]["filters"]["applied"] == {"side": None, "map": None, "format": None, "season": None}

    lado = get(client, f"/api/players/{pid}?lado=t")
    check(lado, "PlayerDetail")
    assert lado["advanced"]["side"] == "t"
    assert lado["advanced"]["rounds"] < base["advanced"]["rounds"]
    # o cabeçalho não muda com o filtro
    assert lado["headline"] == base["headline"]

    mapa = options["maps"][0]
    por_mapa = get(client, f"/api/players/{pid}?mapa={mapa}")
    assert [m["map"] for m in por_mapa["advanced"]["maps"]] == [mapa]
    assert 0 < por_mapa["advanced"]["coverage"]["maps_with_demo"] <= base["advanced"]["coverage"]["maps_with_demo"]

    vazio = get(client, f"/api/players/{pid}?mapa=Mapa-inexistente")
    check(vazio, "PlayerDetail")
    assert vazio["advanced"]["rounds"] == 0 and vazio["advanced"]["coverage"]["maps_with_demo"] == 0
    assert vazio["advanced"]["filters"]["options"] == options

    ignorado = get(client, f"/api/players/{pid}?lado=xyz&formato=bo9&periodo=abc")
    assert ignorado["advanced"]["filters"]["applied"] == base["advanced"]["filters"]["applied"]


def test_perfil_avancado_nomes_com_significado(client, demo):
    _, detail = _first_with_demo(client)
    metrics = [m for ms in detail["advanced"]["sections"].values() for m in ms]
    assert metrics and all(m["label"].isascii() and m["meaning"] for m in metrics)


def test_missions_weekly_status(client):
    data = get(client, "/api/missions")
    week = data["week"]
    assert week and 1 <= week["number"] <= week["total"] and week["starts_on"] <= week["ends_on"]
    assert data["players"], "a demonstração tem jogadores ativos"
    statuses = {p["status"] for p in data["players"]}
    assert statuses <= {"done", "unselected", "open", "none"}
    # Ordenados: cumpridas primeiro, sem partidas por último.
    order = {"done": 0, "unselected": 1, "open": 2, "none": 3}
    ranks = [order[p["status"]] for p in data["players"]]
    assert ranks == sorted(ranks)
    for p in data["players"]:
        assert p["target"] in (0.42, 0.57, 0.72, 0.87, 1.02)
        if p["status"] == "none":
            assert p["maps_in_week"] == 0


def test_missions_week_clipped_in_old_season(client):
    data = get(client, "/api/missions?season=0")
    assert data["week"] is None and data["players"] == []
