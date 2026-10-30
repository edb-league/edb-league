"""Testes do sorteador de times por níveis 1–10, sem acesso ao banco."""

import itertools

import random

from pathlib import Path

import pytest

from edb.team_draw import (
    draw_balanced_teams, draw_message, player_name, player_level,
    team_cards_html,
)

def sample(stars=(5,5,4,4,4,3,3,3,2,1)):
    return [
        {"id":f"id-{i}","nickname":f"nick{i}","real_name":f"Nome {i}",
         "stars":3,"skill_level":value}
        for i,value in enumerate(stars)
    ]

def min_possible_difference(players):
    values=[player_level(p) for p in players]
    total=sum(values)
    return min(abs(total - 2*sum(values[i] for i in indices))
               for indices in itertools.combinations(range(10),5))

def test_balanced_teams_always_split_ten_unique_players():
    players=sample()
    team_a,team_b=draw_balanced_teams(players,random.Random(11))
    assert len(team_a)==len(team_b)==5
    assert {p["id"] for p in team_a+team_b}=={p["id"] for p in players}
    assert abs(sum(player_level(p) for p in team_a)-
               sum(player_level(p) for p in team_b))==min_possible_difference(players)

def test_optimal_balance_for_several_star_distributions():
    cases=[
        (5,5,5,5,5,1,1,1,1,1),
        (4,4,4,4,4,4,4,4,4,4),
        (5,4,4,3,3,3,3,2,2,1),
        (5,5,5,5,4,4,3,2,1,1),
        (1,1,1,1,1,1,1,1,1,2),
        (10,9,9,8,7,7,7,6,5,4),
    ]
    for stars in cases:
        players=sample(stars)
        smallest=min_possible_difference(players)
        for seed in range(10):
            a,b=draw_balanced_teams(players,random.Random(seed))
            assert abs(sum(player_level(p) for p in a)-
                       sum(player_level(p) for p in b))==smallest

def test_sorting_the_selection_does_not_alter_optimality():
    players=sample()
    a,b=draw_balanced_teams(list(reversed(players)),random.Random(3))
    assert {p["id"] for p in a+b}=={p["id"] for p in players}
    assert abs(sum(player_level(p) for p in a)-
               sum(player_level(p) for p in b))==min_possible_difference(players)

def test_sorteio_returns_different_valid_combinations():
    players=sample((3,)*10)
    generator=random.Random(21)
    results=set()
    for _ in range(30):
        a,b=draw_balanced_teams(players,generator)
        results.add(tuple(sorted(p["id"] for p in a)))
        assert sum(player_level(p) for p in a)==15
        assert sum(player_level(p) for p in b)==15
    assert len(results)>1

def test_rejects_non_ten_duplicate_and_invalid_stars():
    players=sample()
    with pytest.raises(ValueError,match="exatamente 10"):
        draw_balanced_teams(players[:9])
    with pytest.raises(ValueError,match="duas vezes"):
        draw_balanced_teams(players[:9]+[players[0]])
    with pytest.raises(ValueError,match="entre 1 e 10"):
        draw_balanced_teams([{**players[0],"skill_level":11},*players[1:]])

def test_cards_are_safe_and_group_copy_matches_balanced_sum():
    roster=sample()
    roster[0]["real_name"]='<img src=x onerror=alert(1)>'
    a,b=draw_balanced_teams(roster,random.Random(1))
    markup=team_cards_html(a,b)
    assert '<img src=x onerror' not in markup
    assert '&lt;img src=x onerror' in markup
    assert 'edb-draw-team--blue' in markup
    assert 'edb-draw-team--red' in markup
    assert '<strong>PT</strong>' in markup
    assert '<strong>PL</strong>' in markup
    assert '<section class="edb-draw-team edb-draw-team--red"><div class="edb-draw-head"><strong>PT</strong>' in markup
    assert '<section class="edb-draw-team edb-draw-team--blue"><div class="edb-draw-head"><strong>PL</strong>' in markup
    assert markup.count('edb-draw-player"')==10
    message=draw_message(a,b)
    assert "EDB LEAGUE" in message
    assert "Diferença:" in message
    assert "🔴 PT" in message
    assert "🔵 PL" in message
    assert "TIME A" not in message and "TIME B" not in message
    assert message.count("• ")==10
    assert player_name(roster[0]) in message
