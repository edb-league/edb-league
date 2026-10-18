"""Regras competitivas da Temporada 1+: seis melhores mapas por ranking."""
from datetime import date, timedelta

import pandas as pd

from season_rankings import season_boards, has_technical_tie


def _rows(total=15, players=("A",), starts=date(2026, 10, 19)):
    data=[]
    for name in players:
        for i in range(total):
            data.append({
                "player_id": name,
                "nickname": name,
                "stars": 3,
                "match_id": f"map{i:02}",
                "played_at": pd.Timestamp(starts + timedelta(days=i % 14)),
                "kills": 5+i,
                "deaths": 10,
                "assists": 2,
                "damage": 400+i*40,
                "rounds": 20,
                "won": bool(i % 2),
            })
    return pd.DataFrame(data)


def test_six_best_maps_and_no_limit_to_total_matches():
    boards=season_boards(_rows(),1,{"A":3})
    elite=boards["elite"].iloc[0]
    supera=boards["superacao"].iloc[0]
    xp=boards["xp"].iloc[0]
    assert elite["Elegível"] == True
    assert elite["Mapas disputados"] == 15
    assert elite["Partidas"] == 6
    assert elite["Mapas selecionados"] == [f"map{i:02}" for i in range(14,8,-1)]
    assert set(supera["Mapas selecionados"]) == set(elite["Mapas selecionados"])
    assert len(xp["Mapas selecionados"]) == 6
    # XP privilegia os mapas vencidos, nao os de maior dano.
    assert xp["Mapas selecionados"] == [f"map{i:02}" for i in (1,3,5,7,9,11)]
    assert 0 <= xp["XP"] <= (6*60+2*100)


def test_ineligible_until_six_valid_maps():
    boards=season_boards(_rows(total=5),1)
    for board in boards.values():
        row=board.iloc[0]
        assert row["Mapas disputados"] == 5
        assert row["Partidas"] == 5
        assert row["Elegível"] == False


def test_stars_are_frozen_for_whole_period():
    data=_rows(total=6)
    data["stars"]=1
    low=season_boards(data,1,{"A":1})["superacao"].iloc[0]
    high=season_boards(data,1,{"A":5})["superacao"].iloc[0]
    assert low["Estrelas"] == 1
    assert high["Estrelas"] == 5
    assert low["Superação %"] > high["Superação %"]


def test_two_independent_sets_of_six_when_adr_differs():
    data=_rows(total=9)
    # Mapa 0: KPR baixo, ADR elevado (bom para Elite).
    data.loc[data["match_id"]=="map00","damage"]=13000
    elite=season_boards(data,1)["elite"].iloc[0]
    superacao=season_boards(data,1)["superacao"].iloc[0]
    assert "map00" in elite["Mapas selecionados"]
    assert "map00" not in superacao["Mapas selecionados"]


def test_tie_detection_checks_actual_full_precision():
    boards=season_boards(_rows(total=6,players=("A","B")),1)
    assert has_technical_tie(boards["elite"],"elite")
    assert has_technical_tie(boards["superacao"],"superacao")
    assert has_technical_tie(boards["xp"],"xp")


def test_legacy_rules_stay_separate():
    data=_rows(total=6)
    old=season_boards(data,0)["elite"]
    new=season_boards(data,1)["elite"]
    assert old.iloc[0]["Elegível"] == True
    assert new.iloc[0]["Partidas"] == 6
    # Regra T0 preserva 4 primeiros jogos por semana.
    assert old.iloc[0]["Partidas"] < 6
