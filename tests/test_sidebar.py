"""Testes de regressão da barra horizontal da EDB LEAGUE."""
from pathlib import Path

APP = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")


def test_brand_and_top_menu_are_loaded():
    assert "page_title='EDB LEAGUE'" in APP
    assert "hero_banner(" in APP
    assert "import brand_shell as _brand_shell" in APP
    assert "import top_navigation as _top_navigation" in APP
    assert "TOP_NAV_CSS, top_navigation(page)" in APP
    assert "initial_sidebar_state='collapsed'" in APP


def test_top_navigation_reads_query_params_and_keeps_player_links():
    assert "st.markdown(" in APP and "'\\n\\n'.join((CSS, BRAND_CSS, TOP_NAV_CSS, top_navigation(page)))" in APP
    assert "requested_page = st.query_params.get('page')" in APP
    assert "st.session_state['edb_page'] = ROUTES[requested_page]" in APP
    assert "linked_player = st.query_params.get('player')" in APP
    assert "st.session_state['edb_page'] = 'Jogadores'" in APP
    assert "player_banner(player_label(who['nickname']),steam," in APP
    assert "st.sidebar" not in APP
    assert "st.sidebar.radio(" not in APP


def test_clean_tabs_and_team_scoreboard_before_match_details():
    assert "st.tabs(['Elite','Superação','Resenha'])" not in APP
    assert "st.markdown(rank_switch(selected_rank, season=season_number), unsafe_allow_html=True)" in APP
    assert "st.tabs(['Geral','Mira','Utilitárias'])" in APP
    matches = APP.split("elif page=='Partidas':",1)[1].split("elif page=='Missões & XP':",1)[0]
    assert matches.index("basic_team_tables(match,t,supplement)") < matches.index(
        "st.tabs(['Geral','Mira','Utilitárias'])"
    )
    assert "edb-score-team" in matches
    assert "Ver placar e estatísticas" not in matches or "Placar da partida" in matches


def test_match_metadata_follows_scoreboards_and_stats():
    matches = APP.split("elif page=='Partidas':",1)[1].split("elif page=='Missões & XP':",1)[0]
    assert matches.index("st.markdown('#### Placar da partida')") < matches.index(
        "st.tabs(['Geral','Mira','Utilitárias'])"
    )
    assert matches.index("st.tabs(['Geral','Mira','Utilitárias'])") < matches.index(
        'st.caption(f"Fonte: {source}'
    )
    assert matches.index('st.caption(f"Fonte: {source}') < matches.index(
        "if match.get('notes'):st.caption(match['notes'])"
    )


def test_player_profiles_and_hall_of_fame_reachable():
    assert "elif page=='Hall da Fama':" in APP
    assert "linked_player = st.query_params.get('player')" in APP
    assert "player_banner(player_label(who['nickname']),steam," in APP
    assert "render_hall_of_fame(" in APP
    assert "def get_career_records():" in APP
    assert "return match_records(all_players,all_matches,all_stats,scope_stats)" in APP


def test_comparison_and_medal_pages_accessible():
    assert "ROUTES = _top_navigation.ROUTES" in APP
    assert "elif page=='Comparar jogadores':" in APP
    assert "elif page=='Medalhas':" in APP
    assert "player_medals=" in APP
    assert "render_medal_catalogue(" in APP
    assert "compare_players(first_id,second_id,career_records)" in APP


def test_page_banner_follows_top_nav_without_extra_toolbar():
    assert "st.markdown(" in APP and "'\\n\\n'.join((CSS, BRAND_CSS, TOP_NAV_CSS, top_navigation(page)))" in APP
    assert "frame['match_id'].astype(str).isin(season_ids)" in APP
    assert "st.selectbox('Filtrar partidas por período'," not in APP
    assert "with st.container(key='edb_period_toolbar')" not in APP
    assert "top_counters(len(all_players)" not in APP
    assert "CSS, BRAND_CSS, TOP_NAV_CSS" in APP
    assert "unique_maps = len({" in APP


def test_profile_and_awards_are_reachable_without_sidebar():
    assert "elif page=='Comparar jogadores':" in APP
    assert "elif page=='Medalhas':" in APP
    assert "elif page=='Hall da Fama':" in APP
    assert "elif page=='Jogadores':" in APP
    assert "elif page=='Administração':" in APP
    assert "player_medals=" in APP
    assert "def get_career_records():" in APP
    assert "return match_records(all_players,all_matches,all_stats,scope_stats)" in APP
    assert "render_medal_catalogue(" in APP
    assert "render_hall_of_fame(" in APP


def test_styles_are_not_rendered_as_empty_blocks_before_menu():
    assert "st.markdown(CSS,unsafe_allow_html=True)" not in APP
    assert "st.markdown(BRAND_CSS,unsafe_allow_html=True)" not in APP
    assert "st.markdown(TOP_NAV_CSS,unsafe_allow_html=True)" not in APP
    assert "'\\n\\n'.join((CSS, BRAND_CSS, TOP_NAV_CSS, top_navigation(page)))" in APP
