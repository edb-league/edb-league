"""Layout regression checks for ranking explanation and player comparison columns."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.py").read_text(encoding="utf-8")
COMPARISON = (ROOT / "social_views.py").read_text(encoding="utf-8")


def test_elite_explanation_follows_ranking_cards():
    ranks=APP.split("elif page=='Rankings':",1)[1].split("elif page=='Comparar jogadores':",1)[0]
    assert ranks.index("scoreboard_table(board.sort_values('Elite'") < ranks.index(
        "with st.expander('Como funciona o Índice Elite')"
    )
    assert ranks.index("with st.expander('Como funciona o Índice Elite')") < ranks.index(
        "with b:"
    )
    assert "Índice = 100" in ranks


def test_comparison_column_names_replace_ab_and_metric_is_clean():
    assert '<div class="edb-duel-metric-label">Métrica</div>' in COMPARISON
    assert '<div class="edb-duel-value edb-duel-column-name">' in COMPARISON
    assert "escape(names[0])" in COMPARISON
    assert "escape(names[1])" in COMPARISON
    assert 'edb-duel-value">A</div>' not in COMPARISON
    assert 'edb-duel-value">B</div>' not in COMPARISON
    assert "Métrica · <span" not in COMPARISON


def test_vertical_player_separator_stretches_through_stats():
    assert ".edb-duel-metric > .edb-duel-value:last-child" in COMPARISON
    assert "border-left:1px solid #5A7290" in COMPARISON
    assert "align-items:stretch" in COMPARISON
    assert "@media(max-width:650px)" in COMPARISON
