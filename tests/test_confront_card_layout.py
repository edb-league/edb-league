"""Apresentação das BO1 à esquerda e BO3 à direita, PT/PL e placares reais."""
from html import unescape
from pathlib import Path

from season_system import bo3_cards

CSS=(Path(__file__).resolve().parents[1]/"season_system.py").read_text("utf-8")


def fixture():
    series=[
        {"id":"series-3","season_number":1,"sequence_number":3,"match_format":"bo1",
         "team_a_name":"PT","team_b_name":"PL","winner_side":"b",
         "status":"completed","played_on":"2026-10-19"},
        {"id":"series-1","season_number":1,"sequence_number":1,"match_format":"bo3",
         "team_a_name":"PT","team_b_name":"PL","winner_side":"a",
         "status":"completed","played_on":"2026-10-21"},
        {"id":"series-2","season_number":1,"sequence_number":2,"match_format":"bo1",
         "team_a_name":"PL","team_b_name":"PT","winner_side":"a",
         "status":"completed","played_on":"2026-10-20"},
    ]
    links=[
        {"series_id":"series-3","match_id":"bo1-pl","map_number":1,"winner_side":"b"},
        {"series_id":"series-1","match_id":"first","map_number":1,"winner_side":"a"},
        {"series_id":"series-1","match_id":"second","map_number":2,"winner_side":"b"},
        {"series_id":"series-1","match_id":"last","map_number":3,"winner_side":"a"},
        {"series_id":"series-2","match_id":"bo1-reversed","map_number":1,"winner_side":"a"},
    ]
    matches=[
        {"id":"bo1-pl","played_at":"2026-10-19","map_name":"Overpass",
         "team_a_score":6,"team_b_score":13},
        {"id":"first","played_at":"2026-10-19","map_name":"Anubis"},
        {"id":"second","played_at":"2026-10-20","map_name":"Mirage"},
        {"id":"last","played_at":"2026-10-21","map_name":"Inferno"},
        {"id":"bo1-reversed","played_at":"2026-10-20","map_name":"Dust2",
         "team_a_score":13,"team_b_score":6},
    ]
    return series,links,matches


def rendered():
    return bo3_cards(1,*fixture())


def test_bo1_comes_first_and_bo3_second_even_if_series_numbers_interleave():
    html=rendered()
    bo1,bo3=html.split('<section class="edb-series-column" aria-label="BO3">')
    assert '<section class="edb-series-column" aria-label="BO1">' in bo1
    assert "BO1 - 20/10/2026" in bo1
    assert "BO1 - 19/10/2026" in bo1
    assert "BO3 - 19/10/2026" not in bo1
    assert "BO3 - 19/10/2026" in bo3
    assert 'edb-series-columns' in html
    assert 'grid-template-columns:repeat(2,minmax(0,1fr))' in html


def test_first_bo3_map_date_not_last_or_series_date():
    html=rendered()
    assert "BO3 - 19/10/2026" in html
    assert "BO3 - 21/10/2026" not in html
    assert "BO3 #1" not in html


def test_known_pt_pl_always_left_right_regardless_of_recorded_order():
    html=rendered()
    # Overpass is A=PT (6), B=PL (13), B wins
    assert ('<span class="edb-series-team edb-series-team--pt">PT</span>'
            '<span class="edb-series-number edb-series-number--lose">6</span>'
            '</div><span class="edb-series-versus" aria-hidden="true">×</span>'
            '<div class="edb-series-side edb-series-side--right">'
            '<span class="edb-series-number edb-series-number--win">13</span>'
            '<span class="edb-series-team edb-series-team--pl">PL</span>') in html
    # Dust2 is stored A=PL (13), B=PT (6), A wins; display STILL PT 6 × 13 PL
    assert html.count('edb-series-number--win">13</span>')==2
    assert html.count('edb-series-number--lose">6</span>')==2
    # BO3 PT won 2:1 and must show green left/red right
    assert ('edb-series-number--win">2</span>') in html
    assert ('edb-series-number--lose">1</span>') in html


def test_click_routes_and_selected_state_preserved():
    html=bo3_cards(1,*fixture(),selected_series="series-3")
    assert 'href="?page=matches&amp;season=1&amp;bo3=series-1"' in html
    assert 'href="?page=matches&amp;season=1"' in html
    assert "edb-series-selected" in html
    assert "FECHAR ↑" in html


def test_no_fabricated_pt_pl_when_legacy_unidentified():
    series=[{"id":"legacy","season_number":0,"sequence_number":1,
             "status":"draft","winner_side":None,
             "team_a_name":"Time 1","team_b_name":"Time 2"}]
    html=bo3_cards(0,series,[],[])
    assert "BO3 - Data a definir" in html
    assert "Time 1" in html and "Time 2" in html
    assert "PT" not in html.split("edb-series-scoreboard",1)[1]
    assert "edb-series-number--win" in CSS
    assert "edb-series-number--lose" in CSS
