"""Remoção segura de participantes do elenco, com históricos intactos."""
import sqlite3
from pathlib import Path

import pytest

from storage import Store

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/"app.py").read_text(encoding="utf-8")
STORAGE=(ROOT/"storage.py").read_text(encoding="utf-8")


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


def test_admin_removes_without_delete_and_restores_from_separate_list():
    assert "active_players=[p for p in all_players if bool(p.get('is_active',True))]" in APP
    assert "inactive_players=[p for p in all_players if not bool(p.get('is_active',True))]" in APP
    assert "ordered=sorted(active_players,key=lambda p:player_name(p).casefold())" in APP
    assert "k1.metric('Jogadores ativos',len(active_players))" in APP
    assert "if len(active_players) < 2:" in APP
    assert "render_medal_catalogue(st,active_players,player_medals)" in APP
    assert "def get_career_records():" in APP
    assert "return cached_career_records(all_players,all_matches,all_stats,scope_stats)" in APP
    assert "with st.form('edb_archive_player'):" in APP
    assert "st.form_submit_button('Remover jogador',type='primary')" in APP
    assert "if not remove_confirm:" in APP
    assert "store.set_player_active(remove_target['id'],False)" in APP
    assert "with st.form('edb_reactivate_player'):" in APP
    assert "store.set_player_active(reactivate_target['id'],True)" in APP
    assert "invalidate_league_cache()" in APP
    assert "self._api('PATCH', 'players'" in STORAGE
    assert "DELETE FROM players" not in STORAGE
