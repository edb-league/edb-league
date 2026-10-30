"""Remoção segura de participantes do elenco, com históricos intactos."""

import sqlite3

from pathlib import Path

import pytest

from edb.storage import Store

def test_archiving_player_preserves_stats_and_prevents_draw_selection(tmp_path):
    store=Store(db_file=tmp_path/"league.db")
    player_id=store.save_player("Participante",stars=3,skill_level=8)
    store.save_match(
        {"id":"map-1","played_at":"2026-10-19","map_name":"Mirage",
         "source":"teste","rounds_total":20,"notes":None},
        [{"match_id":"map-1","player_id":player_id,"kills":19,
          "deaths":13,"assists":5,"rounds":20,"won":1,
          "headshots":8,"plants":0,"defuses":0}]
    )
    assert store.players()[0]["is_active"]==1
    assert store.stats()[0]["kills"]==19

    store.set_player_active(player_id,False)
    record=store.players()[0]
    assert record["id"]==player_id
    assert record["is_active"]==0
    assert store.stats()[0]["kills"]==19
    assert len(store.matches())==1

    # Nova importação não altera o estado de um cadastro já removido.
    assert store.save_player("Participante",stars=3)==player_id
    assert store.players()[0]["is_active"]==0

    store.set_player_active(player_id,True)
    assert store.players()[0]["is_active"]==1
    assert store.stats()[0]["kills"]==19

def test_player_status_validated_and_unknown_id_rejected(tmp_path):
    store=Store(db_file=tmp_path/"league.db")
    player_id=store.save_player("Teste",skill_level=5)
    with pytest.raises(ValueError,match="Jogador não encontrado"):
        store.set_player_active("id-inexistente",False)
    with pytest.raises(ValueError,match="válidos"):
        store.set_player_active(player_id,0)
    with pytest.raises(ValueError,match="válidos"):
        store.set_player_active("",True)
    assert store.players()[0]["is_active"]==1

def test_older_sqlite_files_gain_active_column_without_data_loss(tmp_path):
    path=tmp_path/"old_league.db"
    with sqlite3.connect(path) as conn:
        conn.execute(
            "CREATE TABLE players (id TEXT PRIMARY KEY, nickname TEXT NOT NULL,"
            " steamid TEXT UNIQUE, stars INTEGER NOT NULL DEFAULT 3,"
            " skill_level INTEGER NOT NULL DEFAULT 5)"
        )
        conn.execute(
            "INSERT INTO players (id,nickname,stars,skill_level)"
            " VALUES ('legacy','Veterano',3,7)"
        )
    store=Store(db_file=path)
    assert store.players()[0]["is_active"]==1
    assert store.players()[0]["nickname"]=="Veterano"
    store.set_player_active("legacy",False)
    assert store.players()[0]["is_active"]==0
