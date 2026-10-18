"""Garante o desenho angular somente nas três abas de ranking."""
from pathlib import Path

APP = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")


def test_ranking_navigation_keeps_three_functional_tabs():
    assert "with st.container(key='edb_ranking_tabs'):" in APP
    assert "a,b,c=st.tabs(['Elite','Superação','Resenha'])" in APP
    assert "with a:" in APP and "with b:" in APP and "with c:" in APP
    assert "focus='Elite'" in APP
    assert "focus='Superação %'" in APP
    assert "focus='XP'" in APP


def test_angular_blue_nav_is_scoped_to_ranking_only():
    assert ".st-key-edb_ranking_tabs [data-testid=\"stTabs\"]" in APP
    assert "clip-path:polygon(11px 0" in APP
    assert "button[aria-selected=\"true\"]" in APP
    assert "background:#80D1FF" in APP
    assert "button[role=\"tab\"] p" in APP
    # Histórico de partidas e administração mantêm as próprias tabs.
    assert "st.tabs(['Geral','Mira','Utilitárias'])" in APP
    assert "st.tabs(['👥 Jogadores','📁 Importar demo / CSV','⬇️ Exportar dados'])" in APP


def test_player_cards_keep_independent_rounded_corners():
    RANKING = (Path(__file__).resolve().parents[1] / "ranking_cards.py").read_text(encoding="utf-8")
    assert "border-radius:18px" in RANKING
    assert "edb-rank-card" in RANKING
