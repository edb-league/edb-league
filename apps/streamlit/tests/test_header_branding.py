"""Regression tests for EDB branded top navigation from user references."""
import base64
from pathlib import Path

from top_navigation import NAV_ITEMS, TOP_NAV_CSS, _crest_image, top_navigation


def test_user_crest_is_embedded_and_has_valid_webp_signature():
    crest = _crest_image()
    decoded = base64.b64decode(crest, validate=True)
    assert decoded[:4] == b"RIFF"
    assert decoded[8:12] == b"WEBP"
    assert len(decoded) > 1000
    markup = top_navigation("Medalhas")
    assert '<img src="data:image/webp;base64,' in markup
    assert 'alt="Brasão EDB LEAGUE"' in markup
    assert 'class="edb-topbrand"' in markup
    assert '<span class="edb-topbrand-name">EDB LEAGUE</span>' in markup


def test_current_tab_uses_cyan_underline_and_not_filled_pill():
    markup = top_navigation("Medalhas")
    assert 'aria-label="Medalhas" aria-current="page"' in markup
    assert 'class="edb-nav-item edb-nav-selected"' in markup
    assert 'a.edb-nav-selected:after' in TOP_NAV_CSS
    assert "background:#65C4FC" in TOP_NAV_CSS
    assert "color:#91D4FF" in TOP_NAV_CSS
    assert 'background:transparent;' in TOP_NAV_CSS


def test_brand_is_left_of_categories_and_header_moves_up():
    markup = top_navigation("Medalhas")
    assert markup.index('class="edb-topbrand"') < markup.index('class="edb-topnav"')
    assert markup.index("edb-topbrand-name") < markup.index('aria-label="Visão geral"')
    assert 'class="edb-admin-float' in markup
    assert "padding-top:0 !important" in TOP_NAV_CSS
    assert "overflow-x:auto" in TOP_NAV_CSS
    assert "@media(max-width:650px)" in TOP_NAV_CSS
    assert [label for _, label, _ in NAV_ITEMS] == [
        "Visão geral", "Rankings", "Partidas", "Jogadores", "Comparar jogadores",
        "Hall da Fama", "Medalhas", "Missões & XP",
    ]


def test_top_has_no_default_streamlit_gutter():
    assert '[data-testid="stMainBlockContainer"], .block-container' in TOP_NAV_CSS
    assert "padding-top:0 !important" in TOP_NAV_CSS
    assert 'margin-top:0 !important' in TOP_NAV_CSS
