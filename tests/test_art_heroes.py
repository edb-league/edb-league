"""Verifica banners ilustrados e preservação de dados reais nas telas EDB."""
import base64
from pathlib import Path

from brand_shell import BRAND_CSS, hero_banner


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.py").read_text(encoding="utf-8")
SOCIAL = (ROOT / "social_views.py").read_text(encoding="utf-8")
FAME = (ROOT / "legacy_views.py").read_text(encoding="utf-8")


def test_three_hero_images_are_valid_embedded_webp_files():
    for name in ("duel", "medals", "trophy"):
        path = ROOT / "assets" / f"{name}.webp.b64"
        raw = base64.b64decode(path.read_text(encoding="ascii"), validate=True)
        assert len(raw) > 2000
        assert raw[:4] == b"RIFF"
        assert raw[8:12] == b"WEBP"


def test_all_three_pages_use_their_distinct_artwork():
    for page in ("Comparar jogadores", "Medalhas", "Hall da Fama", "Rankings", "Partidas", "Missões & XP", "Visão geral"):
        markup = hero_banner(page, "Mensagem", 11, 3, 3, page=page)
        assert '<img class="edb-art-image"' in markup
        assert 'data:image/webp;base64,' in markup
        expected = ('class="hero edb-hero edb-hero--illustrated edb-hero--duel"'
                    if page == "Comparar jogadores"
                    else 'class="hero edb-hero edb-hero--illustrated edb-hero--hall"'
                    if page == "Hall da Fama"
                    else 'class="hero edb-hero edb-hero--illustrated edb-hero--showcase"')
        assert expected in markup
        assert '<div class="edb-radar"' not in markup
    assert ".edb-hero--illustrated" in BRAND_CSS
    assert "@media(max-width:650px)" in BRAND_CSS


def test_unrelated_pages_keep_default_radar_without_using_artwork():
    markup = hero_banner("Jogadores", "Perfis", 11, 3, 3, page="Jogadores")
    assert '<div class="edb-radar"' in markup
    assert 'data:image/webp;base64,' not in markup


def test_comparison_and_medals_keep_real_data():
    assert "render_compare(st,px,by_id[first_id],by_id[second_id]" in APP
    assert "compare_players(first_id,second_id,career_records)" in APP
    assert "render_medal_catalogue(st,active_players,player_medals)" in APP
    assert "Medalhas conquistadas" in SOCIAL
    assert 'len(earned)' in SOCIAL
    assert "Jogadores premiados" in SOCIAL
    assert "Temporada 3" not in FAME
    assert 'top = sorted(by_player.values()' in FAME
    assert "Destaque da liga" in FAME
    assert "edb-fame-overview" not in FAME
    assert "Recordes ativos" not in FAME


def test_comparison_selectors_follow_approved_copy():
    assert "st.selectbox('Selecionar jogador 1'" in APP
    assert "st.selectbox('Selecionar jogador 2'" in APP
    assert '<div class="edb-duel-metric-label">Jogador</div>' in SOCIAL


def test_desktop_comparison_uses_full_resolution_art_and_full_bleed():
    raw = base64.b64decode((ROOT / "assets" / "duel.webp.b64").read_text(encoding="ascii"), validate=True)
    # Replace the previous tiny demo art (few KB) with a real high-resolution asset.
    assert len(raw) > 120_000
    assert raw[8:12] == b"WEBP"
    assert "edb-hero--duel .edb-hero-art" in BRAND_CSS
    assert "edb-hero--duel .edb-art-image" in BRAND_CSS
    assert "object-fit:cover;object-position:center center;" in BRAND_CSS
    assert "flex:0 1 40%;max-width:40%" in BRAND_CSS
    assert "edb-hero--duel" not in hero_banner("Medalhas", "Conquistas", 11, 3, 3, page="Medalhas")


def test_desktop_hall_uses_full_resolution_trophy_and_full_bleed():
    image_data = (ROOT / "assets" / "trophy.webp.b64").read_text(encoding="ascii")
    raw = base64.b64decode(image_data, validate=True)
    assert len(raw) > 180_000
    assert raw[:4] == b"RIFF"
    assert raw[8:12] == b"WEBP"
    assert "edb-hero--hall .edb-hero-art" in BRAND_CSS
    assert "edb-hero--hall .edb-art-image" in BRAND_CSS
    assert ".edb-hero--hall .edb-hero-copy" in BRAND_CSS
    assert "edb-hero--hall" not in hero_banner("Medalhas", "Conquistas", 11, 3, 3, page="Medalhas")


def test_medals_and_rankings_use_new_2172x724_desktop_art():
    for asset, page in (("medals", "Medalhas"), ("rankings", "Rankings")):
        raw = base64.b64decode(
            (ROOT / "assets" / f"{asset}.webp.b64").read_text(encoding="ascii"),
            validate=True,
        )
        assert len(raw) > 200_000
        assert raw[:4] == b"RIFF"
        assert raw[8:12] == b"WEBP"
        markup = hero_banner(page, "Texto de demonstração", 11, 3, 3, page=page)
        assert 'edb-hero--illustrated edb-hero--showcase' in markup
        assert '<img class="edb-art-image"' in markup
        assert "data:image/webp;base64," in markup
    assert ".edb-hero--showcase .edb-hero-art" in BRAND_CSS
    assert ".edb-hero--showcase .edb-art-image" in BRAND_CSS
    assert "object-fit:cover;object-position:center center;" in BRAND_CSS
    assert "flex:0 1 40%;max-width:40%" in BRAND_CSS
    assert "edb-hero--duel" not in hero_banner("Medalhas", "", 11, 3, 3, page="Medalhas")
    assert "edb-hero--hall" not in hero_banner("Rankings", "", 11, 3, 3, page="Rankings")


def test_partidas_and_missoes_xp_have_distinct_full_bleed_high_resolution_art():
    art_set = set()
    for asset, page in (("matches", "Partidas"), ("xp", "Missões & XP")):
        raw = base64.b64decode(
            (ROOT / "assets" / f"{asset}.webp.b64").read_text(encoding="ascii"),
            validate=True,
        )
        assert len(raw) > 200_000
        assert raw[:4] == b"RIFF" and raw[8:12] == b"WEBP"
        art_set.add(raw)
        markup = hero_banner(page, "Desempenho real", 11, 3, 3, page=page)
        assert 'class="hero edb-hero edb-hero--illustrated edb-hero--showcase"' in markup
        assert 'data:image/webp;base64,' in markup
        assert '<div class="edb-radar"' not in markup
        assert "Desempenho real" in markup
    assert len(art_set) == 2
    assert '.edb-hero--showcase .edb-art-image' in BRAND_CSS
    assert 'flex:0 1 40%;max-width:40%' in BRAND_CSS
    assert 'object-fit:cover;object-position:center center;' in BRAND_CSS


def test_home_banner_uses_approved_2172x724_desktop_image_not_radar():
    raw = base64.b64decode(
        (ROOT / "assets" / "home.webp.b64").read_text(encoding="ascii"),
        validate=True,
    )
    assert len(raw) > 140_000
    assert raw[:4] == b"RIFF" and raw[8:12] == b"WEBP"
    markup = hero_banner("Página inicial", "Uma liga de CS2", 11, 3, 3, page="Visão geral")
    assert 'class="hero edb-hero edb-hero--illustrated edb-hero--showcase"' in markup
    assert 'data:image/webp;base64,' in markup
    assert '<div class="edb-radar"' not in markup
    assert '.edb-hero--showcase .edb-art-image' in BRAND_CSS
    assert "hero('Os Xinxas agora têm ranking.'" in APP


def test_home_season_rules_banner_below_elite_and_draw():
    assert 'def season_rules_banner(selected_season):' in APP
    assert '1 mês' in APP
    assert 'Do dia 19 ao dia 18 do mês seguinte' in APP
    assert 'BO3 livres' in APP
    assert 'Top 6 mapas' in APP
    assert 'A cada temporada, uma nova disputa começa' in APP
    assert 'Cada novo mapa pode melhorar sua classificação.' in APP
    assert 'Para concorrer aos títulos, é necessário disputar pelo menos 6 mapas.' in APP
    assert 'Todos os resultados ficam registrados no histórico da liga.' in APP
    assert 'As regras abaixo entram em vigor a partir da Temporada 1' not in APP
    assert '.edb-season-rules-grid' in APP
    overview = APP.split("if page=='Visão geral':", 1)[1].split("elif page=='Rankings':",1)[0]
    assert overview.index("home_elite,home_president=st.columns(2,gap='large')") < overview.index(
        "with home_elite:"
    )
    assert overview.index("with home_elite:") < overview.index("st.plotly_chart(fig,use_container_width=True)")
    assert overview.index("st.plotly_chart(fig,use_container_width=True)") < overview.index(
        "with home_president:"
    )
    assert overview.index("with home_president:") < overview.index("render_president_banner()")
    assert overview.index("render_president_banner()") < overview.index(
        "with st.container(key='edb_home_draw'):"
    )
    assert overview.index("with st.container(key='edb_home_draw'):") < overview.index(
        "render_home_team_draw()"
    )
    assert overview.index("render_home_team_draw()") < overview.index(
        "st.markdown(season_rules_banner(season_number)"
    )


class _FakeSt:
    def __init__(self):
        self.blocks = []

    def markdown(self, body, **kwargs):
        self.blocks.append(body)

    def info(self, body, **kwargs):
        self.blocks.append("INFO:" + body)

    def __getattr__(self, name):
        return lambda *args, **kwargs: None


def _hall_entries():
    return [
        {"title": "Mais kills em uma partida", "value": "28 kills",
         "holders": [{"id": "1", "name": "Kvra (Caveira)"}], "detail": "Mirage · 20/10/2026"},
        {"title": "Maior ADR em uma partida", "value": "103.2 ADR",
         "holders": [{"id": "2", "name": "Alfa"}], "detail": "Anubis · 19/10/2026"},
        {"title": "Mais vitórias", "value": "3 vitórias",
         "holders": [{"id": "3", "name": "Bravo"}, {"id": "4", "name": "Charlie"}],
         "detail": "Acumulado em todas as partidas registradas"},
    ]


def test_hall_has_four_squares_in_requested_order():
    from legacy_views import render_hall, LEGACY_CSS
    fake = _FakeSt()
    render_hall(fake, _hall_entries(), 5, players=[], records=[])
    duo = next(block for block in fake.blocks if 'class="edb-fame-duo"' in block)
    assert duo.count("<section") == 4
    order = [duo.index(text) for text in (
        "MELHOR MARCA INDIVIDUAL", "PRÊMIO HENIO",
        "MAIOR ADR EM UMA PARTIDA", "MAIS VITÓRIAS")]
    assert order == sorted(order)
    assert "28 kills" in duo and "103.2 ADR" in duo and "3 vitórias" in duo
    assert "Bravo</a> · <a" in duo and "Charlie" in duo
    assert "aspect-ratio:1/1" in LEGACY_CSS
    assert "grid-template-columns:repeat(4,minmax(0,300px))" in LEGACY_CSS
    assert "@media(max-width:1279px){.edb-fame-duo{grid-template-columns:repeat(2" in LEGACY_CSS
    assert ".edb-fame-duo{grid-template-columns:minmax(0,1fr)}" in LEGACY_CSS


def test_hall_skips_squares_without_data_and_keeps_the_henio_square():
    from legacy_views import render_hall
    fake = _FakeSt()
    render_hall(fake, [], 0, players=[], records=[])
    duo = next(block for block in fake.blocks if 'class="edb-fame-duo"' in block)
    assert duo.count("<section") == 1 and "edb-fame-spotlight" not in duo
    assert any(block.startswith("INFO:") for block in fake.blocks)
    partial = _FakeSt()
    render_hall(partial, _hall_entries()[:1], 1, players=[], records=[])
    duo = next(block for block in partial.blocks if 'class="edb-fame-duo"' in block)
    assert duo.count("<section") == 2 and "MAIOR ADR" not in duo


def test_hall_keeps_css_for_every_section_below_the_squares():
    import re
    from legacy_views import render_hall, LEGACY_CSS
    records = [
        {"player_id": "1", "player_name": "Alfa", "kills": 20},
        {"player_id": "2", "player_name": "Bravo", "kills": 10},
    ]
    fake = _FakeSt()
    render_hall(fake, _hall_entries(), 5, players=[], records=records)
    markup = " ".join(block for block in fake.blocks if "<" in block)
    used = set(re.findall(r'class="([^"]+)"', markup))
    classes = {name for group in used for name in group.split()}
    assert {"edb-fame-top-player", "edb-fame-toplist", "edb-fame-grid", "edb-fame-card"} <= classes
    missing = sorted(name for name in classes
                     if name.startswith("edb-") and "." + name not in LEGACY_CSS)
    assert not missing, f"classes sem CSS: {missing}"
