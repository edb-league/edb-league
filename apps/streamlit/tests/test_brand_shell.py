"""Check responsive identity, data-driven counters, and safe banner content."""
from brand_shell import BRAND_CSS, sidebar_header, hero_banner


def test_sidebar_live_counts_and_active_period():
    markup = sidebar_header(11, 3, 496, "Temporada inteira")
    assert 'class="edb-brand"' in markup
    assert "EDB LEAGUE" in markup
    assert "11</strong>" in markup
    assert "3</strong>" in markup
    assert "496</strong>" in markup
    assert "Temporada inteira" in markup
    assert "Counter-Strike" not in markup or "COUNTER-STRIKE 2" in markup


def test_banner_has_tactical_art_and_real_counts():
    markup = hero_banner("Histórico de partidas", "Mapas e resultados", 11, 3, 3)
    assert 'class="hero edb-hero"' in markup
    assert 'class="edb-radar"' in markup
    assert "Histórico de partidas" in markup
    assert "Mapas e resultados" in markup
    assert "Jogadores" in markup
    assert "Partidas" in markup
    assert "Mapas" in markup
    assert markup.count('class="edb-hero-chip"') == 3
    assert "84%" not in markup
    assert "92%" not in markup


def test_mobile_adaptive_hero_and_escape_user_content():
    assert "@media(max-width:650px)" in BRAND_CSS
    assert "grid-template-columns:minmax(0,1fr)" in BRAND_CSS
    assert "border-radius:18px" in BRAND_CSS
    header=sidebar_header(2,1,3,'<script>x</script>')
    banner=hero_banner('<img src=x>', '<script>x</script>', 1, 0, 0)
    assert '<script>' not in header
    assert '<script>' not in banner
    assert '<img src=x>' not in banner
    assert "&lt;img src=x&gt;" in banner


def test_compact_sidebar_brand_has_air_below_navigation_and_no_tagline():
    markup = sidebar_header(11, 3, 496, "Temporada inteira")
    assert "Uma temporada, várias formas de vencer." not in markup
    assert "edb-brand-desc" not in markup
    assert "margin-top:-18px;margin-bottom:26px" in BRAND_CSS
    assert "EDB LEAGUE" in markup
    assert "COUNTER-STRIKE 2" in markup
