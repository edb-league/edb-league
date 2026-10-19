"""A quarta otimizacao reduz trabalho no rerun sem alterar regras da liga."""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/"app.py").read_text(encoding="utf-8")
BRAND=(ROOT/"brand_shell.py").read_text(encoding="utf-8")


def test_imports_are_not_reloaded_on_every_streamlit_rerun():
    assert "importlib.reload(" not in APP
    assert "import importlib" not in APP
    for name in ("fixture_cards", "match_cards", "season_system", "season_rankings",
                 "ranking_cards", "ranking_navigation", "league_legacy", "legacy_views",
                 "league_social", "social_views", "brand_shell", "top_navigation"):
        assert f"import {name} as _{name}" in APP


def test_calendar_rpc_runs_on_hourly_cache_and_daily_key():
    assert "@st.cache_data(ttl=3600, max_entries=4, show_spinner=False)" in APP
    assert "def ensure_current_calendar(supabase_url: str, _service_role_key: str, brasil_date: str)" in APP
    assert "datetime.now(TZ).date().isoformat()" in APP
    assert "ensure_current_calendar(supabase_url,_service_role_key," in APP
    assert APP.count("'POST','rpc/ensure_edb_calendar',payload={}") == 1


def test_computations_cache_in_cloud_but_not_sqlite():
    assert "def cached_enriched_frame(" in APP
    assert "def cached_season_boards(" in APP
    assert "def cached_career_records(" in APP
    assert "return cached_career_records(all_players,all_matches,all_stats,scope_stats)" in APP
    assert "return match_records(all_players,all_matches,all_stats,scope_stats)" in APP
    assert "if store.cloud else season_boards(selected,season_number,season_stars)" in APP
    assert "else enrich(all_players,all_matches,all_stats)" in APP
    assert "ttl=60, max_entries=12" in APP


def test_admin_writes_clear_derived_and_source_caches():
    start=APP.index("def invalidate_league_cache():")
    end=APP.index("\nif store.cloud:",start+5)
    block=APP[start:end]
    for name in ("load_league_snapshot", "load_scope_stats", "cached_enriched_frame",
                 "cached_season_boards", "cached_career_records"):
        assert f"{name}.clear()" in block
    assert APP.count("invalidate_league_cache()") == 7


def test_art_and_historical_rules_remain_unchanged():
    assert 'data:image/webp;base64,' in BRAND
    assert '/app/static/' not in BRAND
    assert "if int(season_number) == 0:" in (ROOT/"season_rankings.py").read_text(encoding="utf-8")
    assert "season_boards(selected,season_number,season_stars)" in APP
