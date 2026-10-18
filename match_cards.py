"""Grade de partidas (até três por linha) com placares reais e links para detalhes."""
from __future__ import annotations

from html import escape
from urllib.parse import quote
import re
import pandas as pd

from fixture_cards import fixture_overview


MATCH_GRID_CSS = """
<style>
/* Cards de confrontos: três por linha no desktop, com detalhes fora da grade. */
.edb-match-grid {
  display:grid;
  grid-template-columns:repeat(3,minmax(0,1fr));
  gap:17px;
  align-items:stretch;
  margin:17px 0 24px;
}
.edb-match-card {
  display:flex;flex-direction:column;gap:0;min-width:0;
  min-height:205px;box-sizing:border-box;
  padding:19px 18px 15px;
  border:1px solid #36536E;border-radius:16px;
  background:linear-gradient(135deg,#172E45 0%,#102236 100%);
  text-decoration:none !important;color:#E8F3FC !important;
  box-shadow:0 6px 21px rgba(0,0,0,.17);
  transition:transform .15s ease,border-color .15s ease,background .15s ease;
}
.edb-match-card:hover,.edb-match-card:focus-visible {
  border-color:#77B6E5;
  background:linear-gradient(135deg,#203E5A,#152B41);
  transform:translateY(-2px);
}
.edb-match-card.edb-match-card--active {
  border-color:#8BCFFF;
  box-shadow:inset 0 0 0 1px rgba(138,207,255,.35),0 7px 24px rgba(0,0,0,.20);
}
.edb-match-top {
  display:flex;align-items:center;justify-content:space-between;
  gap:8px;min-width:0;
}
.edb-match-map {
  font-size:.77rem;font-weight:900;letter-spacing:.12em;
  color:#B9DFFF;min-width:0;overflow-wrap:anywhere;
}
.edb-match-date {font-size:.72rem;color:#92ADC5;white-space:nowrap;}
.edb-match-versus {
  display:grid;grid-template-columns:minmax(0,1fr) auto minmax(0,1fr);
  align-items:center;gap:6px;flex:1;margin:19px 0 15px;
}
.edb-match-side {display:flex;flex-direction:column;align-items:center;
  justify-content:center;min-width:0;gap:5px;text-align:center;}
.edb-match-side-name {
  font-weight:850;font-size:.79rem;line-height:1.25;color:#D6E3EF;
  overflow-wrap:anywhere;
}
.edb-match-side-status {
  font-size:.55rem;font-weight:800;letter-spacing:.09em;
  color:#7791AA;text-transform:uppercase;
}
.edb-match-side--win .edb-match-side-name,
.edb-match-side--win .edb-match-side-status {color:#88CFFF;}
.edb-match-side--loss .edb-match-side-name,
.edb-match-side--loss .edb-match-side-status {color:#F6A0A8;}
.edb-match-result {display:flex;align-items:center;justify-content:center;
  gap:5px;white-space:nowrap;font-variant-numeric:tabular-nums;}
.edb-match-result b {font-size:1.8rem;font-weight:900;color:#E4F1FC;}
.edb-match-result b.edb-match-number--win {color:#83C9FF;}
.edb-match-result b.edb-match-number--loss {color:#F08D98;}
.edb-match-result span {font-size:1.17rem;color:#7190A9;font-weight:700;}
.edb-match-bottom {
  display:flex;justify-content:space-between;align-items:center;
  gap:8px;border-top:1px solid #334D65;padding-top:12px;
}
.edb-match-bottom span {font-size:.63rem;color:#88A2B9;}
.edb-match-bottom strong {font-size:.68rem;color:#A5D9FC;white-space:nowrap;}
.edb-match-expanded-head {
  display:flex;align-items:center;justify-content:space-between;
  gap:10px;flex-wrap:wrap;border:1px solid #42617D;border-radius:15px;
  background:linear-gradient(115deg,#1A3650,#11283D);
  padding:18px 20px;margin:12px 0 18px;
}
.edb-match-expanded-head strong {color:#F0F7FF;font-size:1.1rem;}
.edb-match-expanded-head a {color:#93D0F5 !important;font-size:.8rem;
  text-decoration:none !important;font-weight:750;}
@media(max-width:1050px) {
  .edb-match-grid {grid-template-columns:repeat(2,minmax(0,1fr));}
}
@media(max-width:690px) {
  .edb-match-grid {grid-template-columns:minmax(0,1fr);gap:12px;}
  .edb-match-card {min-height:183px;}
}
</style>
"""


def match_sort_key(match):
    """Ordena data/hora real, sem depender da ordem incidental do banco."""
    played = pd.to_datetime(match.get("played_at"), errors="coerce")
    if pd.isna(played):
        played = pd.Timestamp("1900-01-01")
    notes = str(match.get("notes") or "")
    # Se o registro tiver apenas data, usa o horário documentado nas notas.
    if played.hour == 0 and played.minute == 0 and played.second == 0:
        found = re.search(r"(?<!\d)([01]\d|2[0-3]):([0-5]\d)(?::([0-5]\d))?(?!\d)", notes)
        if found:
            played += pd.Timedelta(hours=int(found.group(1)),
                                   minutes=int(found.group(2)),
                                   seconds=int(found.group(3) or 0))
    return played, str(match.get("id") or "")


def ordered_matches(matches):
    return sorted(matches, key=match_sort_key, reverse=True)


def _side_class(winner, side):
    if winner is None:
        return "", "EQUIPE"
    if winner == side:
        return " edb-match-side--win", "VENCEDOR"
    return " edb-match-side--loss", "DERROTADO"


def match_cards(matches, selected_id=None):
    """Cartões totalmente clicáveis; sem placares estimados ou dados inventados."""
    pieces = [MATCH_GRID_CSS, '<div class="edb-match-grid">']
    for match in ordered_matches(matches):
        item = fixture_overview(match)
        match_id = str(match["id"])
        active = match_id == str(selected_id)
        left_class, left_status = _side_class(item["winner"], "left")
        right_class, right_status = _side_class(item["winner"], "right")
        a = str(item["score_left"]) if item["verified"] else "—"
        b = str(item["score_right"]) if item["verified"] else "—"
        a_tint = " edb-match-number--win" if item["winner"] == "left" else (
            " edb-match-number--loss" if item["winner"] == "right" else "")
        b_tint = " edb-match-number--win" if item["winner"] == "right" else (
            " edb-match-number--loss" if item["winner"] == "left" else "")
        url = ("?page=matches" if active else
               "?page=matches&amp;match=" + quote(match_id, safe=""))
        aria = escape(
            f"{item['map']} {item['date']}: {item['left']} {a} a {b} {item['right']}. "
            + ("Fechar detalhes" if active else "Ver placar e estatísticas"),
            quote=True)
        css_class = ' edb-match-card--active' if active else ''
        pieces.append(
            '<a class="edb-match-card' + css_class + '" href="' + url +
            '" target="_self" aria-label="' + aria + '">'
            '<div class="edb-match-top">'
            '<span class="edb-match-map">' + escape(item["map"]) + '</span>'
            '<time class="edb-match-date">' + escape(item["date"]) + '</time></div>'
            '<div class="edb-match-versus">'
            '<div class="edb-match-side' + left_class + '">'
            '<span class="edb-match-side-name">' + escape(item["left"]) + '</span>'
            '<span class="edb-match-side-status">' + left_status + '</span></div>'
            '<div class="edb-match-result">'
            '<b class="' + a_tint.strip() + '">' + a + '</b>'
            '<span>:</span><b class="' + b_tint.strip() + '">' + b + '</b></div>'
            '<div class="edb-match-side' + right_class + '">'
            '<span class="edb-match-side-name">' + escape(item["right"]) + '</span>'
            '<span class="edb-match-side-status">' + right_status + '</span></div></div>'
            '<div class="edb-match-bottom"><span>' +
            ("PLACAR VERIFICADO" if item["verified"] else "PLACAR PENDENTE") +
            '</span><strong>' +
            ("FECHAR DETALHES ↑" if active else "VER ESTATÍSTICAS ↓") +
            '</strong></div></a>'
        )
    return "".join(pieces) + "</div>"


def selected_match_header(match):
    info = fixture_overview(match)
    score = f"{info['score_left']} : {info['score_right']}" if info["verified"] else "— : —"
    heading = " · ".join((info["map"], info["date"],
                          f"{info['left']} {score} {info['right']}"))
    return ('<div class="edb-match-expanded-head"><strong>' + escape(heading) +
            '</strong><a href="?page=matches" target="_self">Fechar detalhes ✕</a></div>')
