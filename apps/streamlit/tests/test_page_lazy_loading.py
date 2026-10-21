"""Carregamento sob demanda: rankings, carreira e detalhes de partidas."""
import ast
from pathlib import Path

APP=(Path(__file__).resolve().parents[1]/"app.py").read_text(encoding="utf-8")


def test_career_stats_not_calculated_on_home_or_ranking_start():
    assert "def get_career_records():" in APP
    assert "return cached_career_records(all_players,all_matches,all_stats,scope_stats)" in APP
    assert "return match_records(all_players,all_matches,all_stats,scope_stats)" in APP
    assert "career_records=match_records(all_players,all_matches,all_stats,all_scope_stats)" not in APP
    assert APP.count("career_records=get_career_records()")==4
    sections=APP.split("elif page=='")
    for page in ("Rankings", "Partidas", "Missões & XP", "Administração"):
        section=next(s for s in sections if s.startswith(page+"'"))
        assert "career_records=get_career_records()" not in section
    home=APP.split("if page=='Visão geral':",1)[1].split("elif page=='Rankings':",1)[0]
    assert "get_career_records()" not in home
    assert "hall_of_fame(career_records)" not in home


def test_season_ranking_is_computed_only_on_three_ranking_pages():
    assert "if page in ('Visão geral','Rankings','Missões & XP'):" in APP
    assert "cached_season_boards(selected,season_number,tuple(sorted(season_stars.items())))" in APP
    assert "if store.cloud else season_boards(selected,season_number,season_stars)" in APP
    assert "return enrich(players,matches,stats)" in APP
    assert "frame=enrich(all_players,all_matches,all_stats)" in APP
    top_level=ast.parse(APP).body
    for node in top_level:
        if isinstance(node,ast.Assign):
            calls=[n for n in ast.walk(node) if isinstance(n,ast.Call)]
            assert not any(isinstance(call.func,ast.Name) and call.func.id in {
                "enrich", "match_records", "season_boards", "hall_of_fame", "achievements"
            } for call in calls)


def test_scope_details_load_only_with_page_consumers():
    start=APP.index("def load_league_snapshot(")
    end=APP.index("def load_scope_stats(",start)
    assert "'scope_stats'" not in APP[start:end]
    assert "def get_scope_stats():" in APP
    assert "def get_career_records():" in APP
    assert "all_scope_stats=get_scope_stats()" in APP
    assert "if match is not None:" in APP
    assert "match_stats=[stat for stat in all_stats if str(stat.get('match_id'))==str(match['id'])]" in APP
    assert "t=enrich(all_players,[match],match_stats)" in APP


def test_hall_and_medal_values_remain_real_and_lazy():
    assert "all_time_records=hall_of_fame(career_records)" in APP
    assert "player_medals={str(p['id']):achievements(str(p['id']),career_records) for p in active_players}" in APP
    assert "render_medal_catalogue(st,active_players,player_medals)" in APP
    assert "render_hall_of_fame(st,all_time_records,len(all_matches),all_players,career_records)" in APP
    assert "compare_players(first_id,second_id,career_records)" in APP


def test_previous_cache_and_original_banner_stay_in_place():
    assert "@st.cache_data(ttl=60, max_entries=4, show_spinner=False)" in APP
    assert "invalidate_league_cache()" in APP
    brand=(Path(__file__).resolve().parents[1]/"brand_shell.py").read_text(encoding="utf-8")
    assert 'data:image/webp;base64,' in brand
    assert '/app/static/' not in brand
