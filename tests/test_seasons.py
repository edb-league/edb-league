"""Temporadas EDB: 5 BO3, cronologia, vínculo explícito e rankings isolados."""
from datetime import date
from pathlib import Path

from season_system import (
    DEFAULT_SEASONS, bo3_cards, chosen_season_number, confirmed_bo3_count,
    current_season_number, season_bar, season_match_ids, series_maps,
)


def _series():
    result = []
    for season in (0, 1):
        for n in range(1, 6):
            result.append({"id":f"s{season}bo3{n}","season_number":season,
                           "sequence_number":n,"status":"draft","winner_side":None,
                           "team_a_name":None,"team_b_name":None})
    return result


def test_season_zero_and_one_boundary_is_october_nineteenth():
    assert [s["bo3_target"] for s in DEFAULT_SEASONS] == [3, 5]
    assert current_season_number(DEFAULT_SEASONS,date(2026,10,18)) == 0
    assert current_season_number(DEFAULT_SEASONS,date(2026,10,19)) == 1
    assert current_season_number(DEFAULT_SEASONS,date(2026,11,30)) == 1
    assert chosen_season_number(DEFAULT_SEASONS,date(2026,10,19),"0") == 0
    assert chosen_season_number(DEFAULT_SEASONS,date(2026,10,18),"1") == 1
    assert chosen_season_number(DEFAULT_SEASONS,date(2026,10,18),"abc") == 0


def test_no_unlinked_match_is_counted_as_a_season_map():
    series=_series()
    mapping=[{"series_id":"s0bo31","match_id":"mapA","map_number":1},
             {"series_id":"s0bo31","match_id":"mapB","map_number":2},
             {"series_id":"s1bo31","match_id":"mapC","map_number":1}]
    assert season_match_ids(0,series,mapping)=={"mapA","mapB"}
    assert season_match_ids(1,series,mapping)=={"mapC"}
    assert "legacy-map" not in season_match_ids(0,series,mapping)
    assert confirmed_bo3_count(0,series,mapping)==0
    assert confirmed_bo3_count(1,series,mapping)==0


def test_completed_series_requires_status_winner_and_two_mapped_games():
    series=_series()
    match_links=[{"series_id":"s0bo31","match_id":"m1","map_number":1},
                 {"series_id":"s0bo31","match_id":"m2","map_number":2},
                 {"series_id":"s1bo31","match_id":"m3","map_number":1}]
    series[0]["status"]="completed"
    series[0]["winner_side"]="a"
    assert confirmed_bo3_count(0,series,match_links)==1
    assert confirmed_bo3_count(1,series,match_links)==0
    series[0]["winner_side"]=None
    assert confirmed_bo3_count(0,series,match_links)==0


def test_three_legacy_draft_slots_no_fake_matches_and_links_are_scoped():
    matches=[{"id":"old","map_name":"Anubis","played_at":"2026-09-29"}]
    layout=bo3_cards(0,_series()[:3],[],matches)
    assert layout.count('class="edb-series-card"')==3
    for x in range(1,4):
        assert f"BO3 #{x}" in layout
    assert "0 de até 3 mapas" in layout
    assert "AGUARDANDO REGISTRO" in layout
    assert "2 : 0" not in layout
    assert 'href="?page=matches&amp;season=0&amp;bo3=s0bo31"' in layout
    assert "s1bo31" not in layout


def test_season_selector_persists_rank_mode_and_has_no_extra_period_filter():
    result=season_bar(DEFAULT_SEASONS,1,"rankings",0,rank="resenha")
    assert "Temporada 1" in result and "0 de 5 BO3 concluídas" in result
    assert 'href="?page=rankings&amp;season=0&amp;ranking=resenha"' in result
    assert 'href="?page=rankings&amp;season=1&amp;ranking=resenha"' in result
    assert 'edb-season-active' in result
    assert "Filtrar partidas por período" not in result


def test_selected_series_maps_are_ordered_and_never_fabricated():
    links=[{"series_id":"s0bo31","match_id":"b","map_number":2},
           {"series_id":"s0bo31","match_id":"a","map_number":1},
           {"series_id":"s1bo31","match_id":"c","map_number":1}]
    matches=[{"id":"a","map_name":"Mirage"},{"id":"b","map_name":"Dust2"}]
    assert [x["map_name"] for x in series_maps("s0bo31",links,matches)]==["Mirage","Dust2"]
    assert series_maps("s1bo31",links,matches)==[]


def test_real_app_filters_rankings_by_linked_bo3_maps():
    app=(Path(__file__).resolve().parents[1]/"app.py").read_text(encoding="utf-8")
    assert "all_seasons=store._list('league_seasons')" in app
    assert "all_bo3=store._list('bo3_series')" in app
    assert "all_bo3_maps=store._list('bo3_maps')" in app
    assert "season_number=chosen_season_number(all_seasons,today,requested_season)" in app
    assert "season_ids=season_match_ids(season_number,all_bo3,all_bo3_maps)" in app
    assert "frame['match_id'].astype(str).isin(season_ids)" in app
    assert "bo3_cards(season_number,all_bo3,all_bo3_maps,all_matches,active_bo3_id)" in app
