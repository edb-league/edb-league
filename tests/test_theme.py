"""Checks that the EDB visual palette stays consistent across views."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.py").read_text(encoding="utf-8")
RANK = (ROOT / "ranking_cards.py").read_text(encoding="utf-8")
FIXTURE = (ROOT / "fixture_cards.py").read_text(encoding="utf-8")
CONFIG = (ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8")


def test_primary_color_is_blue_in_streamlit_and_app():
    assert 'primaryColor="#78B8E8"' in CONFIG
    assert 'backgroundColor="#0A1220"' in CONFIG
    assert '#78B8E8' in APP
    assert "st.markdown(TOP_NAV_CSS,unsafe_allow_html=True)" in APP


def test_ranking_uses_subtle_champagne_not_neon_green():
    assert '#D6B98A' in RANK
    assert '#C7AA7D' in RANK
    assert '#D6B98A' in APP
    assert 'border-radius:18px' in RANK


def test_scoreboards_keep_blue_winners_and_red_losers():
    assert '.edb-team-win' in FIXTURE
    assert '.edb-team-loss' in FIXTURE
    assert '#59A9FA' in FIXTURE
    assert '#F07586' in FIXTURE


def test_no_old_neon_palette():
    for source in (APP, RANK, FIXTURE, CONFIG):
        assert '#B6F35D' not in source
        assert '#A8E64C' not in source
        assert '#263D32' not in source



def test_minimal_streamlit_toolbar_preserves_blue_theme():
    assert '[client]' in CONFIG
    assert 'toolbarMode="minimal"' in CONFIG
    assert '#78B8E8' in APP
    assert '[data-testid="stToolbar"],' not in APP
    assert 'toolbarMode="minimal"' in CONFIG
    assert '[data-testid="stSidebarCollapsedControl"] button' not in APP
