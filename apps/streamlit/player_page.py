"""Banner da aba Jogadores: foto da Steam, horas de CS e estatísticas."""
from __future__ import annotations

from html import escape
from urllib.parse import quote

_SILHOUETTE_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96">'
    '<rect width="96" height="96" fill="#2A323C"/>'
    '<circle cx="48" cy="36" r="17" fill="#6F7A87"/>'
    '<path d="M14 96c0-21 15-34 34-34s34 13 34 34z" fill="#6F7A87"/></svg>'
)
SILHOUETTE = "data:image/svg+xml;utf8," + quote(_SILHOUETTE_SVG)

PLAYER_CSS = """
<style>
.edb-player-banner{
  max-width:860px;box-sizing:border-box;margin:14px 0 22px;padding:24px;
  border:1px solid #365A79;border-radius:20px;
  box-shadow:0 12px 28px rgba(0,0,0,.20);
  background:radial-gradient(ellipse at 95% 0%,rgba(85,146,201,.16),transparent 50%),
             linear-gradient(145deg,#142D45 0%,#102237 60%,#0D1B2B 100%);
}
.edb-player-head{display:flex;align-items:center;gap:20px;}
.edb-player-avatar{
  flex:none;width:96px;height:96px;border-radius:50%;object-fit:cover;
  border:2px solid #4C7291;background:#2A323C;
}
.edb-player-id{min-width:0;}
.edb-player-kicker{font-size:.68rem;letter-spacing:1.5px;font-weight:850;color:#8FCBF3;}
.edb-player-name{font-size:1.55rem;font-weight:900;color:#EEF6FF;margin:4px 0 2px;overflow-wrap:anywhere;}
.edb-player-persona{font-size:.78rem;color:#9FB6CA;}
.edb-player-hours{display:flex;align-items:baseline;gap:9px;margin-top:9px;}
.edb-player-hours strong{font-size:1.45rem;font-weight:900;color:#E9D09E;font-variant-numeric:tabular-nums;}
.edb-player-hours span{font-size:.68rem;letter-spacing:1.2px;font-weight:800;color:#B9A585;}
.edb-player-note{font-size:.72rem;color:#8EA6BA;margin-top:3px;}
.edb-player-stats{
  display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;
  margin-top:20px;padding-top:18px;border-top:1px solid rgba(135,170,205,.20);
}
.edb-player-stat{
  background:rgba(8,20,34,.38);border:1px solid rgba(135,170,205,.18);
  border-radius:12px;padding:11px 13px;min-width:0;
}
.edb-player-stat b{display:block;font-size:1.25rem;font-weight:850;color:#EFF6FD;font-variant-numeric:tabular-nums;}
.edb-player-stat span{font-size:.7rem;color:#9DB5CB;}
@media(max-width:600px){
  .edb-player-banner{padding:18px 15px;}
  .edb-player-head{gap:14px;}
  .edb-player-avatar{width:76px;height:76px;}
  .edb-player-name{font-size:1.25rem;}
  .edb-player-stats{grid-template-columns:repeat(2,minmax(0,1fr));}
}
</style>
"""


def format_hours(hours):
    """Horas inteiras (milhar com espaço, para não confundir com decimal)."""
    if hours is None:
        return "—"
    if hours == 0:
        return "0 h"
    if hours < 10:
        return f"{hours:.1f} h"
    return f"{round(hours):,}".replace(",", " ") + " h"


def _num(value, decimals=0):
    if value is None:
        return "–"
    return f"{value:.{decimals}f}" if decimals else str(int(value))


def player_banner(label, steam, summary):
    """HTML do banner; `steam` vem de steam_profile.steam_view e `summary` de player_summary."""
    avatar = steam.get("avatar") or SILHOUETTE
    persona = steam.get("persona") or ""
    games = summary.get("games", 0)
    win_rate = summary.get("win_rate")
    stats = (
        ("Partidas", _num(games)),
        ("Vitórias", _num(summary.get("wins", 0)) if games else "–"),
        ("Aproveitamento", f"{win_rate:.0f}%" if win_rate is not None else "–"),
        ("Kills", _num(summary.get("kills", 0)) if games else "–"),
        ("Mortes", _num(summary.get("deaths", 0)) if games else "–"),
        ("Assistências", _num(summary.get("assists", 0)) if games else "–"),
        ("K/D", _num(summary.get("kd"), 2)),
        ("ADR", _num(summary.get("adr"), 1)),
    )
    note = steam.get("note") or ""
    return (
        PLAYER_CSS +
        '<section class="edb-player-banner">'
        '<div class="edb-player-head">'
        '<img class="edb-player-avatar" src="' + escape(avatar, quote=True) +
        '" alt="Foto de ' + escape(label, quote=True) + '" width="96" height="96">'
        '<div class="edb-player-id">'
        '<div class="edb-player-kicker">PERFIL DO JOGADOR</div>'
        '<div class="edb-player-name">' + escape(label) + '</div>' +
        ('<div class="edb-player-persona">Steam: ' + escape(persona) + '</div>' if persona else '') +
        '<div class="edb-player-hours"><strong>' + escape(format_hours(steam.get("hours"))) +
        '</strong><span>HORAS DE CS</span></div>' +
        ('<div class="edb-player-note">' + escape(note) + '</div>' if note else '') +
        '</div></div>'
        '<div class="edb-player-stats">' + "".join(
            '<div class="edb-player-stat"><b>' + escape(value) + '</b><span>' +
            escape(name) + '</span></div>' for name, value in stats
        ) + '</div></section>'
    )
