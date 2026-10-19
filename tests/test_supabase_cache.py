"""Regressoes do cache temporario de leituras do Supabase."""
from pathlib import Path

APP = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")


def test_snapshot_uses_short_server_side_ttl_and_all_public_tables():
    assert "@st.cache_data(ttl=60, max_entries=4, show_spinner=False)" in APP
    start = APP.index("def load_league_snapshot(")
    end = APP.index("\nstore=Store(", start)
    snapshot = APP[start:end]
    assert "_service_role_key" in snapshot
    assert "ensure_current_calendar(supabase_url,_service_role_key," in snapshot
    assert "'POST','rpc/ensure_edb_calendar',payload={}" in APP
    assert "@st.cache_data(ttl=3600, max_entries=4, show_spinner=False)" in APP
    for table in (
        "players", "matches", "player_stats",
        "league_seasons", "bo3_series", "bo3_maps", "bo3_players",
        "season_player_stars", "season_final_rankings", "season_titles",
    ):
        if table == "players":
            assert "cloud_store.players()" in snapshot
        elif table == "matches":
            assert "cloud_store.matches()" in snapshot
        elif table == "player_stats":
            assert "cloud_store.stats()" in snapshot
        else:
            assert f"cloud_store._list('{table}')" in snapshot
    assert "if store.cloud:\n    snapshot=load_league_snapshot(store.url,store.key)" in APP
    assert "snapshot={" in APP  # SQLite local permanece sem cache.
    assert "'scope_stats': cloud_store._list('player_scope_stats')" not in snapshot
    assert "def load_scope_stats(" in APP
    assert "Store(url=supabase_url,key=_service_role_key)._list('player_scope_stats')" in APP
    assert "def get_scope_stats():" in APP


def test_admin_changes_invalidate_before_rerun():
    assert "def invalidate_league_cache():" in APP
    assert "load_league_snapshot.clear()" in APP
    assert "load_scope_stats.clear()" in APP
    # Duas gravacoes de jogadores, uma de mapa, uma homologacao.
    assert APP.count("invalidate_league_cache()") == 5
    assert "store.save_player(nick,3,steam or None,skill_level=level)\n                    invalidate_league_cache()" in APP
    assert "store.save_player(nn,int(existing['stars']),ss or None,existing['id'],skill_level=level)\n                        invalidate_league_cache()" in APP
    assert "st.session_state.pop('pending_import',None)\n                                invalidate_league_cache()" in APP
    assert "invalidate_league_cache()\n                    st.success('Classificação, estrelas e títulos oficiais homologados.')" in APP
