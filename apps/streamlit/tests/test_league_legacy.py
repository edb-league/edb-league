"""Test all-time records, nick aliases, ties and missing measurements."""
from edb.league_legacy import match_records, player_summary, hall_of_fame
from ranking_cards import ranking_cards


def sample():
    players=[
        {"id":"one","nickname":"SUPERGOV","real_name":"Caveira","stars":4},
        {"id":"two","nickname":"Петэв","real_name":"Pyetev","stars":5},
    ]
    matches=[
        {"id":"m1","played_at":"2026-09-29","map_name":"Mirage"},
        {"id":"m2","played_at":"2026-10-14","map_name":"Dust2"},
    ]
    stats=[
        {"match_id":"m1","player_id":"one","observed_nickname":"cavera",
         "kills":20,"deaths":10,"assists":8,"damage":1600,"rounds":20,"won":True},
        {"match_id":"m2","player_id":"one","observed_nickname":"SUPERGOV",
         "kills":24,"deaths":16,"assists":5,"damage":2200,"rounds":24,"won":False},
        {"match_id":"m1","player_id":"two","observed_nickname":"pyetev",
         "kills":24,"deaths":12,"assists":4,"damage":2100,"rounds":20,"won":False},
        {"match_id":"m2","player_id":"two","observed_nickname":"Петэв",
         "kills":24,"deaths":14,"assists":8,"damage":2300,"rounds":24,"won":True},
    ]
    scope=[
        {"match_id":"m1","player_id":"one","adr_reported":85,
         "grenade_damage":220},
        {"match_id":"m1","player_id":"two","adr_reported":105,
         "grenade_damage":12},
        {"match_id":"m2","player_id":"one","adr_reported":91,
         "grenade_damage":0},
        {"match_id":"m2","player_id":"two","adr_reported":96,
         "grenade_damage":50},
    ]
    return players,matches,stats,scope


def test_aliases_aggregate_under_canonical_player_and_source_adr():
    rows=match_records(*sample())
    assert len(rows)==4
    caveira=player_summary("one",rows)
    assert caveira["games"]==2
    assert caveira["kills"]==44
    assert caveira["wins"]==1
    assert caveira["win_rate"]==50
    assert caveira["kd"]==44/26
    assert caveira["adr"]==3800/44
    assert [r["played_nick"] for r in caveira["matches"]]==["cavera","SUPERGOV"]
    assert caveira["matches"][0]["adr"]==85
    assert caveira["matches"][0]["player_name"]=="Caveira (SUPERGOV)"


def test_hall_maintains_ties_and_stable_identity():
    rows=match_records(*sample())
    titles={record["title"]:record for record in hall_of_fame(rows)}
    assert titles["Mais kills em uma partida"]["value"]=="24 kills"
    assert {h["id"] for h in titles["Mais kills em uma partida"]["holders"]}=={"one","two"}
    assert len(titles["Mais kills em uma partida"]["holders"])==2
    assert titles["Mais kills na liga"]["value"]=="48 kills"
    assert titles["Mais kills na liga"]["holders"][0]["id"]=="two"
    assert titles["Mais dano de granadas"]["holders"][0]["id"]=="one"
    assert titles["Maior ADR em uma partida"]["value"]=="105.0 ADR"
    assert titles["Mais vitórias"]["value"]=="1 vitória"


def test_missing_data_not_promoted_to_fake_records():
    players,matches,stats,scope=sample()
    missing=[{**stats[0], "rounds":0,"damage":None}]
    rows=match_records(players,matches[:1],missing,[])
    assert player_summary("one",rows)["adr"] is None
    labels={r["title"] for r in hall_of_fame(rows)}
    assert "Maior ADR em uma partida" not in labels
    assert "Mais dano de granadas" not in labels
    assert player_summary("missing",rows)["games"]==0


def test_ranking_cards_link_to_player_ids_and_escape_links():
    rows=[{"player_id":"one","Jogador":"Caveira","Estrelas":4,
           "Partidas":2,"Kills":44,"K/D":1.69,"KPR":1,"ADR":86,
           "Vitórias":1,"Elite":120,"Superação %":3,"XP":120,"Elegível":True}]
    content=ranking_cards(rows)
    assert 'href="?player=one"' in content
    assert 'Ver perfil completo' in content
    assert '<article class="edb-rank-card">' in content
