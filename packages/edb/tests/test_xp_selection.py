"""Seleção dos seis mapas do ranking de XP: vitória (60 ou 40) + missão semanal (100 por semana coberta)."""
import itertools
import random
from datetime import date, timedelta

import pandas as pd
import pytest

from edb.season_rankings import _best_xp, _xp_mensal, season_boards

START = date(2026, 10, 15)   # início da temporada 1


def maps(spec, stars=3):
    """spec: lista de (dia da temporada, kills, venceu); 20 rounds por mapa."""
    return pd.DataFrame([{
        "player_id": "A", "nickname": "A", "stars": stars, "match_id": f"m{i:02}",
        "played_at": pd.Timestamp(START + timedelta(days=day)), "kills": kills, "deaths": 10, "assists": 1,
        "damage": 1500, "rounds": 20, "won": won,
    } for i, (day, kills, won) in enumerate(spec)])


def brute_force(frame, stars, season=1):
    best = 0
    for combo in itertools.combinations(range(len(frame)), min(6, len(frame))):
        best = max(best, _xp_mensal(frame.iloc[list(combo)], stars, season))
    return best


def test_mission_beats_a_win_when_it_covers_a_new_week():
    # Cinco vitórias sem missão na semana 1, mais uma derrota com missão na semana 2 e outra vitória fraca.
    spec = [(0, 5, True)] * 5 + [(1, 5, True), (8, 20, False)]
    frame = maps(spec)
    chosen = _best_xp(frame, 3, 1)
    assert "m05" not in set(chosen["match_id"])        # a sétima (vitória sem missão) fica de fora
    assert "m06" in set(chosen["match_id"])            # a derrota com missão entra: +100 > +20
    assert _xp_mensal(chosen, 3, 1) == 5 * 60 + 40 + 100


def test_one_mission_map_per_week_is_enough():
    # Duas missões na mesma semana: só uma entra; a vaga seguinte vai para uma vitória comum.
    spec = [(0, 20, True), (1, 20, True)] + [(8, 5, True)] * 5
    chosen = _best_xp(maps(spec), 3, 1)
    assert len(chosen) == 6
    assert _xp_mensal(chosen, 3, 1) == 6 * 60 + 100


def test_few_maps_are_all_kept():
    frame = maps([(0, 10, True), (3, 20, False)])
    assert list(_best_xp(frame, 3, 1)["match_id"]) == ["m00", "m01"] or set(_best_xp(frame, 3, 1)["match_id"]) == {"m00", "m01"}


@pytest.mark.parametrize("seed", range(40))
def test_selection_is_optimal_against_brute_force(seed):
    rng = random.Random(seed)
    spec = [(rng.randrange(0, 35), rng.randrange(4, 24), rng.random() < 0.5) for _ in range(rng.randrange(7, 12))]
    frame = maps(spec, stars=rng.choice([2, 3, 4]))
    stars = int(frame["stars"].iloc[0])
    chosen = _best_xp(frame, stars, 1)
    assert len(chosen) == 6
    assert _xp_mensal(chosen, stars, 1) == brute_force(frame, stars)


def test_board_uses_the_optimal_selection_and_keeps_tie_break_on_wins():
    frame = maps([(0, 5, True)] * 5 + [(1, 5, True), (8, 20, False)])
    row = season_boards(frame, 1)["xp"].iloc[0]
    assert row["XP"] == 5 * 60 + 40 + 100 and row["Vitórias"] == 5
    assert len(row["Mapas selecionados"]) == 6
