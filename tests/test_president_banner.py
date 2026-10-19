"""Homenagem ao Presidente Dudu e ordem responsiva da pagina inicial."""
from pathlib import Path
import base64

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/"app.py").read_text(encoding="utf-8")
PHOTO=ROOT/"assets"/"president_dudu_hd.avif.b64"


def test_president_photo_is_complete_embedded_hd_avif():
    encoded=PHOTO.read_text(encoding="ascii").strip()
    data=base64.b64decode(encoded,validate=True)
    assert len(data)>20000
    assert b"ftypavif" in data[:32]
    ispe=data.find(b"ispe")
    assert 0<ispe<500
    width=int.from_bytes(data[ispe+8:ispe+12],"big")
    height=int.from_bytes(data[ispe+12:ispe+16],"big")
    assert (width,height)==(540,810)


def test_home_keeps_highlights_above_panels_and_regulations_below():
    overview=APP.split("if page=='Visão geral':",1)[1].split("elif page=='Rankings':",1)[0]
    expected=[
        "st.markdown('### Destaques da temporada')",
        "home_elite,home_president=st.columns(2,gap='large')",
        "with home_elite:",
        "st.plotly_chart(fig,use_container_width=True)",
        "with home_president:",
        "render_president_banner()",
        "with st.container(key='edb_home_draw'):",
        "render_home_team_draw()",
        "st.markdown(season_rules_banner(season_number)",
    ]
    last=-1
    for chunk in expected:
        current=overview.index(chunk)
        assert current>last,chunk
        last=current
    assert "st.container(key='edb_home_president')" in overview
    assert "st.columns(2,gap='large')" in overview
    assert "with home_draw:" not in overview


def test_president_art_and_plaque_are_in_app_not_remote_link():
    assert "def render_president_banner():" in APP
    assert "(ROOT/'assets'/'president_dudu_hd.avif.b64').read_text(" in APP
    assert '<img src="data:image/avif;base64,' in APP
    assert "Inaugurada na gestão do Presidente Dudu" in APP
    assert "19 de outubro de 2026" in APP
    assert ".st-key-edb_home_president" in APP
    assert ".edb-president-photo img" in APP
    assert "object-fit:contain" in APP
    assert ".st-key-edb_home_draw{border-color:#416D90;min-height:0;}" in APP
    assert "return season_boards(" in APP
    assert "data:image/webp;base64," in (ROOT/"brand_shell.py").read_text(encoding="utf-8")
