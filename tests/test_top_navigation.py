"""Testes do novo menu superior, das rotas e do botão de administrador."""
from top_navigation import (
    NAV_ITEMS, ROUTES, TOP_NAV_CSS, top_navigation, top_counters
)


def test_categories_have_exact_requested_order():
    assert [page for slug,page,label in NAV_ITEMS] == [
        "Visão geral", "Rankings", "Partidas", "Comparar jogadores",
        "Hall da Fama", "Medalhas", "Missões & XP"
    ]
    assert "Jogadores" not in [item[1] for item in NAV_ITEMS]
    assert "Administração" not in [item[1] for item in NAV_ITEMS]
    assert ROUTES["players"] == "Jogadores"
    assert ROUTES["admin"] == "Administração"


def test_only_home_is_icon_only_and_navigation_is_clickable():
    markup = top_navigation("Visão geral")
    assert markup.count('class="edb-nav-item') == 7
    assert markup.count('aria-current="page"') == 1
    assert '<svg viewBox="0 0 24 24"' in markup
    assert 'href="?page=home"' in markup
    assert '>Visão geral</a>' not in markup
    for slug,_,_ in NAV_ITEMS:
        assert f'href="?page={slug}"' in markup


def test_admin_button_floats_outside_nav_and_profile_route_exists():
    markup=top_navigation("Administração")
    assert markup.count('class="edb-admin-float') == 1
    assert 'href="?page=admin"' in markup
    assert 'Administrador</a>' in markup
    assert 'edb-admin-selected' in markup
    assert markup.index('</nav>') < markup.index('edb-admin-float')
    assert "position:fixed;left:18px;bottom:18px;" in TOP_NAV_CSS
    assert 'overflow-x:auto' in TOP_NAV_CSS
    assert "@media(max-width:650px)" in TOP_NAV_CSS
    assert '[data-testid="stSidebar"]' in TOP_NAV_CSS


def test_active_category_updates_and_counters_are_not_faked():
    markup=top_navigation("Partidas")
    assert 'aria-label="Partidas" aria-current="page"' in markup
    assert 'aria-label="Rankings" aria-current="false"' in markup
    counters=top_counters(11,3,496)
    assert "11</b> jogadores" in counters
    assert "3</b> partidas" in counters
    assert "496</b> kills registradas" in counters


def test_desktop_menu_is_a_fixed_left_column_and_mobile_keeps_top_bar():
    css = TOP_NAV_CSS
    assert "@media(min-width:861px)" in css
    desktop = css.split("@media(min-width:861px)", 1)[1]
    assert "position:fixed;top:0;left:0;bottom:0;" in desktop
    assert "flex-direction:column;" in desktop
    assert 'padding-left:236px !important' in desktop
    assert "a.edb-nav-selected:after" in desktop
    # Barra horizontal rolável preservada para telas estreitas.
    assert "overflow-x:auto" in css.split("@media(min-width:861px)", 1)[0]
    assert ".edb-nav-home-label {display:none;}" in css


def test_home_label_exists_for_the_side_menu_without_changing_the_link():
    markup = top_navigation("Visão geral")
    assert '<span class="edb-nav-home-label">Visão geral</span>' in markup
    assert 'href="?page=home"' in markup
    assert 'aria-label="Visão geral" aria-current="page"' in markup
    assert markup.count('edb-nav-home-label') == 1
