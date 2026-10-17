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
    assert 'background:#263D32;' in APP
    assert len([x for x in ["Visão geral", "Rankings", "Jogadores",
                           "Partidas", "Missões & XP", "Administração"] if x in APP]) == 6
