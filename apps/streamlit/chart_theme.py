"""Identidade visual compartilhada dos graficos Plotly da EDB LEAGUE.

Este modulo altera exclusivamente aparencia (layout e traces), nunca os valores
ou a classificacao calculados pela liga.
"""
from __future__ import annotations

CHAMPAGNE = "#D6B98A"
BLUE = "#78B8E8"
RED = "#E28787"
TEXT = "#DCEAF5"
GRID = "rgba(135,171,199,0.18)"
AXIS = "#688DAA"


def _base(fig):
    """Eixos ancorados, tipografia e tooltip consistente com o site."""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(12,30,48,0.45)",
        font=dict(color=TEXT, family="Arial, sans-serif", size=12),
        hoverlabel=dict(
            bgcolor="#17324A",
            bordercolor="#527A9B",
            font=dict(color="#F4F8FD", size=12),
        ),
        margin=dict(l=12, r=28, t=18, b=36),
    )
    fig.update_xaxes(
        showline=True, linewidth=2, linecolor=AXIS,
        tickcolor=AXIS, ticks="outside", ticklen=5,
        tickfont=dict(color="#BFD4E5", size=11),
        automargin=True, zeroline=False,
    )
    fig.update_yaxes(
        showline=True, linewidth=2, linecolor=AXIS,
        tickcolor=AXIS, ticks="outside", ticklen=5,
        tickfont=dict(color="#D8E8F4", size=11),
        automargin=True, zeroline=False,
    )
    return fig


def style_edb_bar(fig, *, horizontal=False, grouped=False):
    """Barras com cantos arredondados, eixo de referencia e grid discreto."""
    _base(fig)
    fig.update_layout(
        barcornerradius=9,
        bargap=0.30 if horizontal else 0.24,
        bargroupgap=0.08 if grouped else 0,
    )
    fig.update_traces(
        marker_line_width=0,
        textposition="outside",
        cliponaxis=False,
    )
    if horizontal:
        fig.update_xaxes(
            showgrid=True, gridcolor=GRID, gridwidth=1,
            zeroline=True, zerolinecolor=AXIS, zerolinewidth=2,
            rangemode="tozero",
        )
        fig.update_yaxes(showgrid=False, ticks="")
    else:
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(
            showgrid=True, gridcolor=GRID, gridwidth=1,
            zeroline=True, zerolinecolor=AXIS, zerolinewidth=2,
            rangemode="tozero",
        )
    return fig


def style_edb_line(fig):
    """Linha nítida com pontos em evidência e preenchimento sutil."""
    _base(fig)
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(
        showgrid=True, gridcolor=GRID, gridwidth=1,
        zeroline=True, zerolinecolor=AXIS, zerolinewidth=2,
        rangemode="tozero",
    )
    fig.update_traces(
        mode="lines+markers",
        line=dict(color=BLUE, width=3),
        marker=dict(
            color=BLUE, size=9,
            line=dict(color="#10263B", width=2),
        ),
        fill="tozeroy",
        fillcolor="rgba(120,184,232,0.09)",
        connectgaps=False,
    )
    return fig
