"""Regression tests for displayed matchup titles."""
from fixture_cards import fixture_title, match_stat_coverage

def test_verified_legacy_score():
    match={"map_name":"Dust2","played_at":"2026-10-14","notes":"Placar oficial: Team 1 13–11 Team 2. 23:35"}
    text=fixture_title(match)
    assert "DUST2" in text
    assert "13 : 11" in text
    assert "Team 1" in text and "Team 2" in text

def test_old_team_names_in_notes():
    match={"map_name":"Mirage","played_at":"2026-09-29",
           "notes":"23:47:13, Alfa venceu por 13 a 8 sobre Beta."}
    text=fixture_title(match)
    assert "Alfa" in text and "Beta" in text
    assert "13 : 8" in text

def test_unknown_score_not_guessed_from_round_count():
    match={"map_name":"Anubis","played_at":"2026-10-14",
           "rounds_total":21,"notes":"Team 2 venceu; Team 1 perdeu"}
    text=fixture_title(match)
    assert "— : —" in text
    assert "Team 2" in text and "Team 1" in text

def test_stat_coverage_only_counts_players_from_this_match():
    stats=[
        {"match_id":"m1","player_id":"a","kills":18},
        {"match_id":"m1","player_id":"b","kills":0},
        {"match_id":"m2","player_id":"c","kills":99},
    ]
    extras=[
        {"match_id":"m1","player_id":"a","aim_accuracy_pct":0,
         "grenade_damage":None},
        {"match_id":"m1","player_id":"b","aim_accuracy_pct":None,
         "grenade_damage":0},
        {"match_id":"m1","player_id":"outsider","aim_accuracy_pct":75,
         "grenade_damage":50},
        {"match_id":"m2","player_id":"c","aim_accuracy_pct":45,
         "grenade_damage":99},
    ]
    assert match_stat_coverage("m1",stats,extras)=={
        "players":2,"kills":18,"aim":1,"grenades":1
    }

def test_stat_coverage_handles_absent_scope_data():
    stats=[{"match_id":"m","player_id":"one","kills":4}]
    assert match_stat_coverage("m",stats,[])=={
        "players":1,"kills":4,"aim":0,"grenades":0
    }
    assert match_stat_coverage("missing",stats,[])=={
        "players":0,"kills":0,"aim":0,"grenades":0
    }
