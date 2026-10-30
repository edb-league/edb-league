"""Fluxo híbrido BO1/BO3: mapas, classificações e proteção de históricos."""

from pathlib import Path

from datetime import date

import pytest

from edb.confront_registry import prepare_confront_bundle

from edb.season_system import bo3_cards, confirmed_bo3_count, season_match_ids, series_format

def sample():
    season={"number":1,"starts_on":"2026-10-19","ends_on":"2026-11-01","homologated_at":None}
    matches=[
        {"id":"a","played_at":"2026-10-20","map_name":"Anubis","rounds_total":20},
        {"id":"b","played_at":"2026-10-20","map_name":"Mirage","rounds_total":21},
        {"id":"c","played_at":"2026-10-21","map_name":"Inferno","rounds_total":20},
    ]
    stats=[{"match_id":m["id"],"player_id":f"p{n}"}
           for m in matches for n in range(10)]
    team_a=[f"p{i}" for i in range(5)]
    scores={"a":(13,7),"b":(8,13),"c":(13,7)}
    return season,matches,stats,team_a,scores

def test_bo1_bundles_one_map_and_bo3_bundles_three_without_extra_weight():
    season,matches,stats,roster,scores=sample()
    one=prepare_confront_bundle(
        season,"BO1",["a"],matches,stats,roster,scores
    )
    assert one["format"]=="bo1"
    assert one["season_number"]==1
    assert one["team_a_name"]=="PT" and one["team_b_name"]=="PL"
    assert one["matches"]==[{"match_id":"a","team_a_score":13,"team_b_score":7}]
    three=prepare_confront_bundle(
        season,"BO3",["a","b","c"],matches,stats,roster,scores
    )
    assert three["format"]=="bo3"
    assert [m["match_id"] for m in three["matches"]]==["a","b","c"]

@pytest.mark.parametrize("fmt,ids",[
    ("BO1",["a","b"]),("BO3",["a"]),("BO3",["a","b","b"]),
    ("BO5",["a"]),("BO1",[]),
])
def test_rejects_wrong_format_cardinality_and_duplicate_maps(fmt,ids):
    season,matches,stats,roster,scores=sample()
    with pytest.raises(ValueError):
        prepare_confront_bundle(season,fmt,ids,matches,stats,roster,scores)

def test_rejects_bad_roster_score_missing_data_and_wrong_season():
    season,matches,stats,roster,scores=sample()
    with pytest.raises(ValueError,match="cinco|5"):
        prepare_confront_bundle(season,"BO1",["a"],matches,stats,roster[:4],scores)
    with pytest.raises(ValueError,match="Placar|soma"):
        prepare_confront_bundle(season,"BO1",["a"],matches,stats,roster,{"a":(13,8)})
    with pytest.raises(ValueError,match="empate"):
        prepare_confront_bundle(season,"BO1",["a"],matches,stats,roster,{"a":(10,10)})
    with pytest.raises(ValueError,match="dez"):
        prepare_confront_bundle(season,"BO1",["a"],matches,[row for row in stats if not (row["match_id"]=="a" and row["player_id"]=="p9")],roster,scores)
    with pytest.raises(ValueError,match="fora da temporada"):
        prepare_confront_bundle(
            {**season,"starts_on":"2026-10-22"},"BO1",["a"],matches,stats,roster,scores
        )
    with pytest.raises(ValueError,match="homologada"):
        prepare_confront_bundle(
            {**season,"homologated_at":"2026-11-02"},"BO1",["a"],matches,stats,roster,scores
        )

def test_two_formats_display_correctly_without_altering_old_bo3():
    season,matches,stats,roster,scores=sample()
    series=[
        {"id":"old","season_number":1,"sequence_number":1,
         "status":"completed","winner_side":"a","team_a_name":"PT","team_b_name":"PL"},
        {"id":"new","season_number":1,"sequence_number":2,
         "match_format":"bo1","status":"completed","winner_side":"b",
         "team_a_name":"PT","team_b_name":"PL"},
    ]
    mapping=[
        {"series_id":"old","match_id":"a","map_number":1,"winner_side":"a"},
        {"series_id":"old","match_id":"b","map_number":2,"winner_side":"b"},
        {"series_id":"old","match_id":"c","map_number":3,"winner_side":"a"},
        {"series_id":"new","match_id":"d","map_number":1,"winner_side":"b"},
    ]
    visible=matches+[{"id":"d","played_at":"2026-10-22","map_name":"Dust2",
                      "team_a_score":6,"team_b_score":13}]
    assert series_format(series[0])=="bo3"
    assert series_format(series[1])=="bo1"
    assert confirmed_bo3_count(1,series,mapping)==2
    assert season_match_ids(1,series,mapping)=={"a","b","c","d"}
    cards=bo3_cards(1,series,mapping,visible)
    assert "BO3 - 20/10/2026" in cards
    assert "BO1 - 22/10/2026" in cards
    assert cards.count("FINALIZADA")==2
    assert 'edb-series-number--win">2</span>' in cards
    assert 'edb-series-number--win">13</span>' in cards
    assert 'edb-series-number--lose">6</span>' in cards
    assert cards.index('aria-label="BO1"') < cards.index('aria-label="BO3"')
