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



def test_basic_team_tables_group_teams_and_keep_match_nicks():
    import pandas as pd
    from fixture_cards import basic_team_tables, match_team_names
    match = {"id": "m1", "map_name": "Dust2", "played_at": "2026-10-14",
             "notes": "Placar oficial: Team 1 13–11 Team 2."}
    players = pd.DataFrame([
        {"player_id": "a", "nickname": "Петэв", "observed_nickname": "pyetev",
         "won": True, "kills": 25, "deaths": 14, "assists": 7,
         "damage": 2000, "rounds": 24},
        {"player_id": "b", "nickname": "Bot Bob", "observed_nickname": None,
         "won": False, "kills": 11, "deaths": 20, "assists": 3,
         "damage": None, "rounds": 24},
    ])
    source = [{"match_id": "m1", "player_id": "a", "adr_reported": 113},
              {"match_id": "other", "player_id": "b", "adr_reported": 99}]
    groups = basic_team_tables(match, players, source)
    assert match_team_names(match) == ("Team 1", "Team 2")
    assert len(groups) == 2
    assert [g["name"] for g in groups] == ["Team 1", "Team 2"]
    assert [g["kills"] for g in groups] == [25, 11]
    assert groups[0]["table"].iloc[0]["Jogador"] == "pyetev"
    assert groups[0]["table"].iloc[0]["ADR"] == 113
    assert groups[0]["table"].iloc[0]["K/D"] == 1.79
    assert pd.isna(groups[1]["table"].iloc[0]["ADR"])
    assert groups[1]["table"].iloc[0]["Jogador"] == "Bot Bob"


def test_basic_team_tables_unknown_score_uses_known_winner_only():
    import pandas as pd
    from fixture_cards import basic_team_tables, match_team_names
    match={"id":"m2","map_name":"Anubis","rounds_total":21,
           "notes":"Team 2 venceu; Team 1 perdeu."}
    assert match_team_names(match) == ("Team 2", "Team 1")
    assert basic_team_tables(match, pd.DataFrame(), []) == []
