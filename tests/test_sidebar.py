"""Verificações de regressão da navegação sem depender do Streamlit na CI."""
from pathlib import Path

APP = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")


def test_brand_is_edb_and_no_target_emoji_in_title():
    assert "page_title='EDB LEAGUE'" in APP
    assert "## EDB LEAGUE" in APP
    assert "◆ EDB LEAGUE / CS2" in APP
    assert "## 🎯 XINXAS LEAGUE" not in APP


def test_sidebar_navigation_is_one_click_buttons():
    assert "st.sidebar.radio('Navegação'" not in APP
    assert "for index, (destination, nav_icon) in enumerate(NAVIGATION)" in APP
    assert "on_click=open_page" in APP
    assert "page = st.session_state['edb_page']" in APP
    assert "type='primary' if st.session_state['edb_page'] == destination else 'secondary'" in APP
    assert 'background:#25435F;' in APP
    assert len([x for x in ["Visão geral", "Rankings", "Jogadores",
                           "Partidas", "Missões & XP", "Administração"] if x in APP]) == 6


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
