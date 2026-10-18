"""Verifica botões angulares reais e navegação por URL nos Rankings."""
from pathlib import Path
from ranking_navigation import RANK_OPTIONS, RANK_SWITCH_CSS, rank_switch

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.py").read_text(encoding="utf-8")


def test_three_ranking_buttons_are_real_links_and_keep_order():
    assert RANK_OPTIONS == (("elite","Elite"),("superacao","Superação"),("resenha","Resenha"))
    for current in ("elite","superacao","resenha"):
        markup=rank_switch(current)
        assert markup.count('class="edb-rank-option') == 3
        assert markup.count('aria-current="page"') == 1
        assert markup.count('clip-path:polygon(') >= 3
        assert 'href="?page=rankings&amp;ranking=elite"' in markup
        assert 'href="?page=rankings&amp;ranking=superacao"' in markup
        assert 'href="?page=rankings&amp;ranking=resenha"' in markup
        assert f'aria-label="Ranking {dict(RANK_OPTIONS)[current]}" aria-current="page"' in markup
        assert markup.index('Ranking Elite') < markup.index('Ranking Superação') < markup.index('Ranking Resenha')


def test_active_ranking_has_visible_blue_background_and_glow():
    markup=rank_switch("superacao")
    assert "edb-rank-option--active" in markup
    assert "linear-gradient(120deg,#34749F,#225477)" in markup
    assert "box-shadow:inset 0 -4px #87D6FF;" in markup
    assert "clip-path:polygon(12px 0" in RANK_SWITCH_CSS
    assert "edb-rank-switch" in RANK_SWITCH_CSS
    assert "st-key-edb_ranking_tabs" not in RANK_SWITCH_CSS


def test_categories_switch_real_content_without_streamlit_tabs():
    ranking = APP.split("elif page=='Rankings':",1)[1].split("elif page=='Comparar jogadores':",1)[0]
    assert "st.tabs(['Elite','Superação','Resenha'])" not in APP
    assert "st.markdown(rank_switch(selected_rank), unsafe_allow_html=True)" in ranking
    assert "st.query_params.get('ranking', 'elite')" in ranking
    assert "if selected_rank == 'elite':" in ranking
    assert "elif selected_rank == 'superacao':" in ranking
    assert "elif selected_rank == 'resenha':" in ranking
    assert "focus='Elite'" in ranking
    assert "focus='Superação %'" in ranking
    assert "focus='XP'" in ranking
    assert "st.tabs(['Geral','Mira','Utilitárias'])" in APP


def test_player_cards_keep_independent_rounded_borders():
    source = (ROOT / "ranking_cards.py").read_text(encoding="utf-8")
    assert "border-radius:18px" in source
    assert "edb-rank-card" in source
