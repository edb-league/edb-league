"""Cartões independentes e responsivos para a classificação EDB LEAGUE."""
from __future__ import annotations

from html import escape
from math import isfinite
import pandas as pd

RANKING_CSS = """
<style>
.edb-rank-list{display:flex;flex-direction:column;gap:12px;margin:16px 0 22px}
.edb-rank-card{
  border:1px solid #2C4258;border-radius:18px;
  background:linear-gradient(135deg,#16283B,#111D2D);
  box-shadow:0 4px 14px rgba(0,0,0,.12);
  padding:16px 18px;overflow:hidden;
}
.edb-rank-card:first-child{border-color:#957A55;box-shadow:inset 4px 0 #D6B98A,0 4px 14px rgba(0,0,0,.12)}
.edb-rank-heading{display:flex;align-items:center;justify-content:space-between;gap:12px}
.edb-rank-player{display:flex;align-items:center;gap:12px;min-width:0;flex:1}
.edb-rank-place{font-size:.8rem;font-weight:800;color:#AABED0;min-width:30px}
.edb-rank-identity{min-width:0}
.edb-rank-name{font-size:1rem;font-weight:800;color:#F2F7FC;line-height:1.35;overflow-wrap:anywhere}
.edb-rank-stars{color:#C7AA7D;font-size:.78rem;letter-spacing:1.5px;margin-top:3px}
.edb-rank-focus{text-align:right;flex:none}
.edb-rank-focus-label{color:#A6BACE;text-transform:uppercase;letter-spacing:1px;font-size:.62rem;font-weight:700}
.edb-rank-focus-value{color:#D6B98A;font-size:1.3rem;font-weight:900;font-variant-numeric:tabular-nums;white-space:nowrap}
.edb-rank-divider{border-top:1px solid #2D4156;margin:13px 0 12px}
.edb-rank-metrics{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:9px}
.edb-rank-metric{text-align:left;min-width:0}
.edb-rank-metric-label{font-size:.68rem;color:#9AB0C4}
.edb-rank-metric-value{font-size:.9rem;font-weight:750;color:#E7F2FA;font-variant-numeric:tabular-nums}
.edb-rank-secondary{font-size:.72rem;color:#A1B5C7;margin-top:12px;line-height:1.5}
@media(max-width:640px){
 .edb-rank-card{padding:13px 13px;border-radius:15px}
 .edb-rank-heading{gap:7px}
 .edb-rank-player{gap:7px}
 .edb-rank-name{font-size:.88rem}
 .edb-rank-place{min-width:24px;font-size:.73rem}
 .edb-rank-focus-value{font-size:1.06rem}
 .edb-rank-metrics{grid-template-columns:repeat(3,minmax(0,1fr));gap:12px 8px}
 .edb-rank-secondary{font-size:.67rem}
}
</style>
"""


def _fmt(value, digits=0, suffix=""):
    if value is None or pd.isna(value):
        return "—"
    number = float(value)
    if not isfinite(number):
        return "—"
    return f"{number:.{digits}f}{suffix}"


def ranking_cards(rows, focus="Elite", name_formatter=None):
    """Render each player separately; respect the caller's ranking order."""
    if focus not in ("Elite", "Superação %", "XP"):
        raise ValueError("Ranking desconhecido")
    labels = {"Elite": "Índice Elite", "Superação %": "Superação", "XP": "XP"}
    pieces = ['<div class="edb-rank-list">']
    for index, row in enumerate(rows, 1):
        player = row.get("Jogador", "")
        label = name_formatter(player) if name_formatter else player
        name = escape(str(label))
        stars = max(0, min(int(row.get("Estrelas") or 0), 5))
        score = _fmt(row.get(focus), 1 if focus != "XP" else 0,
                     "%" if focus == "Superação %" else "")
        stats = (
            ("Partidas", _fmt(row.get("Partidas"))),
            ("Kills", _fmt(row.get("Kills"))),
            ("K/D", _fmt(row.get("K/D"), 2)),
            ("KPR", _fmt(row.get("KPR"), 3)),
            ("ADR", _fmt(row.get("ADR"), 1)),
            ("Vitórias", _fmt(row.get("Vitórias"))),
        )
        other = [(key, _fmt(row.get(key), 1 if key != "XP" else 0,
                              "%" if key == "Superação %" else ""))
                 for key in ("Elite", "Superação %", "XP") if key != focus]
        provisional = " · Provisório (menos de 2 partidas)" if row.get("Elegível") is False else ""
        metrics = "".join(
            f'<div class="edb-rank-metric"><div class="edb-rank-metric-label">{title}</div>'
            f'<div class="edb-rank-metric-value">{value}</div></div>'
            for title, value in stats
        )
        lower = " · ".join(f"{labels[key]}: {value}" for key, value in other)
        pieces.append(
            '<article class="edb-rank-card">'
            '<div class="edb-rank-heading">'
            '<div class="edb-rank-player">'
            f'<span class="edb-rank-place">#{index:02d}</span>'
            '<div class="edb-rank-identity">'
            f'<div class="edb-rank-name">{name}</div>'
            f'<div class="edb-rank-stars">{"★" * stars}</div>'
            '</div></div>'
            '<div class="edb-rank-focus">'
            f'<div class="edb-rank-focus-label">{labels[focus]}</div>'
            f'<div class="edb-rank-focus-value">{score}</div>'
            '</div></div>'
            f'<div class="edb-rank-divider"></div><div class="edb-rank-metrics">{metrics}</div>'
            f'<div class="edb-rank-secondary">{lower}{provisional}</div>'
            '</article>'
        )
    pieces.append("</div>")
    return "\n".join(pieces)
