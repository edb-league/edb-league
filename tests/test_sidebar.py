"""Verificações de regressão da navegação sem depender do Streamlit na CI."""
from pathlib import Path

APP = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")


def test_brand_is_edb_and_no_target_emoji_in_title():
    assert "page_title='EDB LEAGUE'" in APP
    assert "sidebar_header(" in APP
    assert "_sidebar_header_slot = st.sidebar.empty()" in APP
    assert "hero_banner(" in APP
    assert "import brand_shell as _brand_shell" in APP
    assert "## 🎯 XINXAS LEAGUE" not in APP


def test_sidebar_navigation_is_one_click_buttons():
    assert "st.sidebar.radio('Navegação'" not in APP
    assert "for index, (destination, nav_icon) in enumerate(NAVIGATION)" in APP
    assert "on_click=open_page" in APP
    assert "page = st.session_state['edb_page']" in APP
    assert "type='primary' if st.session_state['edb_page'] == destination else 'secondary'" in APP
    assert 'background:#25435F;' in APP
    assert len([x for x in ["Visão geral", "Rankings", "Jogadores",
                           "Partidas", "Missões & XP", "Administração", "Hall da Fama",
                           "Comparar jogadores", "Medalhas"] if x in APP]) == 9


def test_clean_tabs_and_team_scoreboard_before_match_details():
    assert "st.tabs(['Elite','Superação','Resenha'])" in APP
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
    assert "('Hall da Fama', ':material/emoji_events:')" in APP
    assert "linked_player = st.query_params.get('player')" in APP
    assert "render_player_profile(" in APP
    assert "render_hall_of_fame(" in APP
    assert "career_records=match_records(" in APP


def test_comparison_and_medal_pages_accessible():
    assert "('Comparar jogadores', ':material/compare_arrows:')" in APP
    assert "elif page=='Comparar jogadores':" in APP
    assert "elif page=='Medalhas':" in APP
    assert "player_medals=" in APP
    assert "render_medal_catalogue(" in APP
    assert "compare_players(first_id,second_id,career_records)" in APP


def test_sidebar_brand_precedes_navigation_and_uses_real_stats():
    assert APP.index("_sidebar_header_slot = st.sidebar.empty()") < APP.index(
        "for index, (destination, nav_icon) in enumerate(NAVIGATION)"
    )
    assert "st.sidebar.markdown('**Navegação**')" not in APP
    assert "season_kills=sum(int(s.get('kills') or 0) for s in all_stats)" in APP
    assert "sidebar_header(len(all_players),len(all_matches),season_kills,period)" in APP
    assert "unique_maps = len({" in APP
    assert "st.markdown(BRAND_CSS,unsafe_allow_html=True)" in APP



def test_native_header_compact_without_losing_sidebar_button():
    assert '[data-testid="stToolbar"]' in APP
    assert '[data-testid="stHeader"]' in APP
    assert '[data-testid="stSidebarCollapsedControl"]' in APP
    assert '#MainMenu' in APP
