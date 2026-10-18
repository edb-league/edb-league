"""Testes de regressao do acabamento visual dos tres graficos Plotly."""
from pathlib import Path
from chart_theme import CHAMPAGNE, BLUE, RED, style_edb_bar, style_edb_line

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/"app.py").read_text(encoding="utf-8")
SOCIAL=(ROOT/"social_views.py").read_text(encoding="utf-8")
LEGACY=(ROOT/"legacy_views.py").read_text(encoding="utf-8")


class FakeFigure:
    """Replica apenas a API de atualizacao do Plotly, sem dependencia grafica no CI."""
    def __init__(self):
        self.layout={}
        self.xaxes={}
        self.yaxes={}
        self.traces={}

    def update_layout(self, **kwargs):
        self.layout.update(kwargs)

    def update_xaxes(self, **kwargs):
        self.xaxes.update(kwargs)

    def update_yaxes(self, **kwargs):
        self.yaxes.update(kwargs)

    def update_traces(self, **kwargs):
        self.traces.update(kwargs)


def test_round_bars_and_defined_axis():
    fig=FakeFigure()
    assert style_edb_bar(fig,horizontal=True) is fig
    assert fig.layout["barcornerradius"]==9
    assert fig.layout["bargap"]==0.30
    assert fig.xaxes["showgrid"] is True
    assert fig.xaxes["zeroline"] is True
    assert fig.xaxes["zerolinewidth"]==2
    assert fig.yaxes["showgrid"] is False
    assert fig.traces["textposition"]=="outside"
    assert fig.traces["cliponaxis"] is False


def test_grouped_bars_have_visible_baseline_and_legend_space():
    fig=FakeFigure()
    assert style_edb_bar(fig,grouped=True) is fig
    assert fig.layout["barcornerradius"]==9
    assert fig.layout["bargroupgap"]==0.08
    assert fig.yaxes["showgrid"] is True
    assert fig.yaxes["zeroline"] is True
    assert fig.xaxes["showgrid"] is False
    assert RED=="#E28787"


def test_line_chart_shows_points_and_subtle_fill():
    fig=FakeFigure()
    assert style_edb_line(fig) is fig
    assert fig.traces["mode"]=="lines+markers"
    assert fig.traces["line"]["width"]==3
    assert fig.traces["marker"]["size"]==9
    assert fig.traces["fill"]=="tozeroy"
    assert fig.traces["connectgaps"] is False
    assert fig.yaxes["showgrid"] is True
    assert fig.xaxes["showline"] is True
    assert BLUE=="#78B8E8"


def test_consistent_site_frames_and_original_images():
    assert 'div[data-testid="stPlotlyChart"]' in APP
    assert "border-radius:18px" in APP
    assert "background:linear-gradient(155deg,#10283F" in APP
    assert "style_edb_bar(fig,horizontal=True)" in APP
    assert "style_edb_bar(fig,grouped=True)" in SOCIAL
    assert "style_edb_line(fig)" in LEGACY
    assert 'color_discrete_sequence=["#78B8E8","#E28787"]' in SOCIAL
    assert "fillcolor" in (ROOT/"chart_theme.py").read_text(encoding="utf-8")
    assert 'data:image/webp;base64,' in (ROOT/"brand_shell.py").read_text(encoding="utf-8")


def test_graphed_values_are_still_sourced_from_original_data():
    assert "px.bar(top.sort_values('Elite'),x='Elite',y='Jogador'" in APP
    assert 'px.bar(pd.DataFrame(chart),x="Partida",y="Kills",color="Jogador"' in SOCIAL
    assert 'px.line(timeline, x="Partida", y=metric' in LEGACY
    assert CHAMPAGNE=="#D6B98A"
