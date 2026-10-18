"""Medalhas e comparação de jogadores: identidade, confrontos e dados faltantes."""
from league_legacy import match_records
from league_social import MEDALS, achievements, compare_players


def sample():
    players=[
        {"id":"a","nickname":"Zbra","real_name":"Dinfas"},
        {"id":"b","nickname":"Петэв","real_name":"Pyetev"},
        {"id":"c","nickname":"Visitor","real_name":"Visitante"},
    ]
    matches=[
        {"id":"m1","played_at":"2026-10-01","map_name":"Mirage"},
        {"id":"m2","played_at":"2026-10-02","map_name":"Dust2"},
        {"id":"m3","played_at":"2026-10-03","map_name":"Anubis"},
    ]
    stats=[
        {"match_id":"m1","player_id":"a","kills":20,"deaths":10,"assists":6,
         "damage":2500,"rounds":21,"won":True,"observed_nickname":"Dinfas"},
        {"match_id":"m1","player_id":"b","kills":15,"deaths":16,"assists":3,
         "damage":1700,"rounds":21,"won":False,"observed_nickname":"pyetev"},
        {"match_id":"m2","player_id":"a","kills":30,"deaths":16,"assists":10,
         "damage":3000,"rounds":24,"won":True,"observed_nickname":"Zbra"},
        {"match_id":"m2","player_id":"b","kills":24,"deaths":12,"assists":5,
         "damage":2600,"rounds":24,"won":True,"observed_nickname":"Петэв"},
        {"match_id":"m3","player_id":"c","kills":5,"deaths":12,"assists":1,
         "damage":None,"rounds":0,"won":None},
    ]
    extras=[
        {"match_id":"m1","player_id":"a","grenade_damage":115,"adr_reported":119},
        {"match_id":"m2","player_id":"a","grenade_damage":0,"adr_reported":125},
        {"match_id":"m1","player_id":"b","grenade_damage":None,"adr_reported":81},
    ]
    return match_records(players,matches,stats,extras)


def test_achievement_thresholds_and_tiers_without_making_up_stats():
    rows=sample()
    earned={medal["id"] for medal in achievements("a",rows) if medal["earned"]}
    assert {"estreia","primeira_vitoria","artilheiro","vinte_balas","trinta_balas",
            "parceiro","artilheiro_utility","precisao"}.issubset(earned)
    assert "regular" not in earned and "exterminador" not in earned
    progress={m["id"]:m for m in achievements("a",rows)}
    assert progress["regular"]["current"] == 2
    assert progress["regular"]["progress"] == 40
    assert progress["artilheiro"]["progress"] == 100
    assert {m["tier"] for m in progress.values()} == {"bronze","silver","gold"}
    visitor={m["id"]:m for m in achievements("c",rows)}
    assert visitor["artilheiro_utility"]["current"] is None
    assert visitor["artilheiro_utility"]["progress"] is None
    assert visitor["precisao"]["current"] is None
    assert not visitor["precisao"]["earned"]
    assert len(MEDALS) == len(set(m["id"] for m in MEDALS))


def test_confronto_direto_only_counts_opposite_teams():
    rows=sample()
    comparison=compare_players("a","b",rows)
    assert comparison["shared_count"] == 2
    assert comparison["opponent_games"] == 1
    assert comparison["teammate_games"] == 1
    assert comparison["head_to_head"] == {"a":1,"b":0}
    assert comparison["shared"][0]["side"] == "Adversários"
    assert comparison["shared"][1]["side"] == "Mesmo time"
    assert comparison["first"]["kills"] == 50
    assert comparison["second"]["kills"] == 39
    assert comparison["first"]["win_rate"] == 100.0
    assert comparison["first"]["matches"][0]["played_nick"] == "Dinfas"
    assert comparison["second"]["matches"][0]["played_nick"] == "pyetev"


def test_compare_no_shared_games_and_same_identity_not_allowed():
    rows=sample()
    empty=compare_players("a","c",rows)
    assert empty["shared_count"] == 0
    assert empty["opponent_games"] == 0
    assert empty["head_to_head"] == {"a":0,"c":0}
    try:
        compare_players("a","a",rows)
    except ValueError:
        pass
    else:
        raise AssertionError("Must require two different players")


def test_unconfirmed_results_not_fake_head_to_head():
    rows=sample()
    first=next(r for r in rows if r["match_id"] == "m1" and r["player_id"] == "a")
    second=next(r for r in rows if r["match_id"] == "m1" and r["player_id"] == "b")
    amended=[{**first, "won":None},second]
    comp=compare_players("a","b",amended)
    assert comp["shared_count"] == 1
    assert comp["opponent_games"] == 0
    assert comp["shared"][0]["side"] == "Lados não confirmados"
