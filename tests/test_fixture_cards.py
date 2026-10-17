"""Regression tests for displayed matchup titles."""
from fixture_cards import fixture_title

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
