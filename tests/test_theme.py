"""Checks that the EDB visual palette stays consistent across views."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.py").read_text(encoding="utf-8")
RANK = (ROOT / "ranking_cards.py").read_text(encoding="utf-8")
FIXTURE = (ROOT / "fixture_cards.py").read_text(encoding="utf-8")
CONFIG = (ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8")


def test_primary_color_is_blue_in_streamlit_and_app():
    assert 'primaryColor="#78B8E8"' in CONFIG
    assert 'backgroundColor="#252930"' in CONFIG
    assert 'linear-gradient(170deg,#30343B 0%,#252930 55%,#1F2329 100%)' in APP
    assert '#78B8E8' in APP
    assert "CSS, BRAND_CSS, TOP_NAV_CSS, top_navigation(page)" in APP


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


def test_only_page_canvas_changes_while_components_stay_blue():
    # Palette for buttons, hero banners, ranking podiums and team results remains unchanged.
    assert '#78B8E8' in APP
    assert '#78B8E8' in CONFIG
    assert 'secondaryBackgroundColor="#15263B"' in CONFIG
    assert 'background:#142337' in APP
    assert 'background:radial-gradient(ellipse at 92% 8%,#254C76' in APP
