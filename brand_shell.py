"""Responsive header artwork and sidebar identity for EDB LEAGUE.

All graphics are CSS/SVG-free HTML shapes, bundled locally (no remote asset).
No fake scores or performance percentages appear in the header.
"""
from __future__ import annotations
from html import escape


BRAND_CSS = """
<style>
/* App shell: compact on tablets, airy on larger screens. */
.block-container {padding-top:1.2rem; max-width:1320px;}
[data-testid="stSidebar"] {
  background:linear-gradient(180deg,#0A1D30 0%,#091827 64%,#081521 100%);
}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {gap:.65rem;}
/* Use the sidebar's full real width and do not style Streamlit's collapse control. */
.edb-brand {
  position:relative;isolation:isolate;overflow:hidden;padding:16px 15px 14px;
  margin-top:-18px;margin-bottom:26px;
  border:1px solid #2C4A67;border-radius:18px;
  background:linear-gradient(135deg,#163451 0%,#102840 48%,#0B2036 100%);
  box-shadow:0 10px 28px rgba(0,0,0,.18);
}
.edb-brand:before {
  content:"";position:absolute;right:-52px;top:-60px;width:150px;height:150px;
  border:1px solid rgba(124,190,245,.17);border-radius:50%;pointer-events:none;
}
.edb-brand:after {
  content:"";position:absolute;right:-25px;top:-26px;width:100px;height:100px;
  border:1px solid rgba(124,190,245,.18);border-radius:50%;pointer-events:none;
}
.edb-brand-row {position:relative;z-index:1;display:flex;align-items:center;gap:11px;}
.edb-brand-mark {
  width:43px;height:43px;flex:none;display:grid;place-items:center;border-radius:12px;
  border:1px solid rgba(139,193,240,.32);
  background:linear-gradient(145deg,#214B71,#17344F);
  font-size:12px;letter-spacing:-.4px;font-weight:950;color:#F6FAFF;
  box-shadow:0 6px 15px rgba(0,0,0,.15);
}
.edb-brand-title {font-size:1.14rem;letter-spacing:.5px;font-weight:900;color:#F5F9FE;line-height:1.12;}
.edb-brand-kicker {font-size:.64rem;letter-spacing:2.2px;font-weight:750;color:#8EC8F1;margin-top:4px;}
.edb-brand-stats {
  position:relative;z-index:1;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));
  gap:6px;margin-top:14px;
}
.edb-brand-stat {
  min-width:0;padding:10px 7px;border-radius:11px;
  background:rgba(6,18,33,.40);border:1px solid rgba(125,176,226,.17);
}
.edb-brand-stat strong {display:block;font-size:1.02rem;font-weight:900;color:#E8F4FF;font-variant-numeric:tabular-nums;}
.edb-brand-stat span {display:block;font-size:.62rem;color:#91B0CE;margin-top:3px;}
.edb-brand-period {position:relative;z-index:1;margin-top:12px;display:flex;
  align-items:center;gap:7px;font-size:.7rem;color:#BBD1E5;}
.edb-brand-period i {display:inline-block;width:6px;height:6px;border-radius:50%;background:#8FC9F2;box-shadow:0 0 0 4px rgba(143,201,242,.10);}
.edb-brand-period b {font-weight:750;color:#EFF6FD;}

/* Hero banner */
.hero.edb-hero {
  position:relative;isolation:isolate;overflow:hidden;margin-bottom:19px;
  padding:25px 27px;border:1px solid #355C80;border-radius:21px;
  display:grid;grid-template-columns:minmax(0,1.25fr) minmax(210px,.75fr);
  gap:20px;min-height:211px;
  background:
    radial-gradient(ellipse at 82% 0%,rgba(90,158,226,.28),transparent 44%),
    linear-gradient(115deg,#152F4D 0%,#102640 53%,#0B1B31 100%);
  box-shadow:0 18px 38px rgba(0,0,0,.16);
}
.edb-hero:after {content:"";pointer-events:none;position:absolute;inset:0;
  background:repeating-linear-gradient(122deg,transparent 0 41px,rgba(185,218,255,.025) 42px 43px,transparent 44px 86px);
}
.edb-hero-copy {position:relative;z-index:2;align-self:center;min-width:0;}
.edb-hero .eyebrow {font-size:.69rem;letter-spacing:2.7px;color:#8FC9F2;}
.edb-hero h1 {font-size:clamp(1.7rem,3.4vw,2.65rem);
  line-height:1.12;letter-spacing:-1px;margin:11px 0 10px;color:#F5F9FE;}
.edb-hero p {font-size:.92rem;line-height:1.55;color:#AFC7DF;max-width:540px;margin:0;}
.edb-hero-chips {display:flex;flex-wrap:wrap;gap:7px;margin-top:20px;}
.edb-hero-chip {
  border:1px solid rgba(139,191,237,.25);background:rgba(7,23,42,.52);
  color:#D9EAF9;border-radius:999px;padding:7px 11px;font-size:.72rem;white-space:nowrap;
}
.edb-hero-chip b {font-weight:900;color:#EFCF9C;margin-right:4px;}
/* Abstract CS-style radar graphic: decorative, no invented game statistics. */
.edb-hero-art {position:relative;z-index:1;min-width:0;min-height:156px;display:grid;place-items:center;}
.edb-radar-grid {position:absolute;inset:0;border-radius:15px;opacity:.36;
  background-image:linear-gradient(rgba(143,195,237,.13) 1px,transparent 1px),
                   linear-gradient(90deg,rgba(143,195,237,.13) 1px,transparent 1px);
  background-size:26px 26px;
  mask-image:radial-gradient(ellipse,black 35%,transparent 76%);
}
.edb-radar {position:relative;width:172px;height:172px;border-radius:50%;
  border:1px solid rgba(143,199,244,.43);box-shadow:0 0 0 15px rgba(89,149,209,.045),0 0 52px rgba(89,149,209,.12);
  background:radial-gradient(circle,rgba(86,153,224,.16) 0%,rgba(6,21,42,.12) 66%,transparent 67%);
}
.edb-radar:before {content:"";position:absolute;inset:26px;border-radius:50%;border:1px dashed rgba(143,199,244,.50);}
.edb-radar:after {content:"";position:absolute;left:50%;top:50%;width:11px;height:11px;transform:translate(-50%,-50%);
  border:1px solid #CBE9FF;background:#81C6FB;border-radius:50%;box-shadow:0 0 0 7px rgba(126,188,240,.12),0 0 23px rgba(143,208,255,.50);}
.edb-radar-axis-h,.edb-radar-axis-v {position:absolute;background:rgba(143,199,244,.36);}
.edb-radar-axis-h {height:1px;left:-8px;right:-8px;top:50%;}
.edb-radar-axis-v {width:1px;top:-8px;bottom:-8px;left:50%;}
.edb-radar-dot {position:absolute;border-radius:50%;background:#D7BB8E;box-shadow:0 0 0 5px rgba(215,187,142,.12);}
.edb-radar-dot.a {left:32px;top:36px;width:8px;height:8px;}
.edb-radar-dot.b {right:29px;bottom:39px;width:6px;height:6px;}
.edb-radar-callout {position:absolute;right:3px;bottom:3px;border:1px solid rgba(137,191,238,.35);
  border-radius:7px;padding:5px 8px;background:#112F4A;color:#ADD2ED;font-size:.62rem;letter-spacing:1.5px;font-weight:800;}
@media(max-width:920px) {
  .hero.edb-hero {grid-template-columns:minmax(0,1fr) 180px;padding:23px 19px;gap:9px;}
  .edb-radar {transform:scale(.84);}
}
@media(max-width:650px) {
  .block-container {padding-top:1rem;}
  .hero.edb-hero {grid-template-columns:minmax(0,1fr);min-height:0;gap:0;padding:19px 17px;border-radius:18px;}
  .edb-hero h1 {font-size:1.9rem;letter-spacing:-.65px;}
  .edb-hero p {font-size:.88rem;}
  .edb-hero-chips {margin-top:15px;gap:6px;}
  .edb-hero-chip {font-size:.67rem;padding:6px 9px;}
  .edb-hero-art {position:absolute;right:-38px;top:-35px;width:155px;height:155px;
    min-height:0;opacity:.20;pointer-events:none;}
  .edb-radar {transform:scale(.82);}
  .edb-hero-copy {padding-right:4px;}
}
</style>
"""


def _fmt(value):
    return f"{int(value):,}".replace(",", ".")


def sidebar_header(players, matches, kills, period):
    """Pure text/html: counts are sourced from the current Streamlit data."""
    safe_period = escape(str(period))
    stats = [("Jogadores", players), ("Partidas", matches), ("Kills", kills)]
    numbers = "".join(
        '<div class="edb-brand-stat"><strong>' + _fmt(number) +
        '</strong><span>' + name + '</span></div>' for name, number in stats
    )
    return (
        '<section class="edb-brand">'
        '<div class="edb-brand-row"><span class="edb-brand-mark">EDB</span>'
        '<div><div class="edb-brand-title">EDB LEAGUE</div>'
        '<div class="edb-brand-kicker">COUNTER-STRIKE 2</div></div></div>'
        '<div class="edb-brand-stats">' + numbers + '</div>'
        '<div class="edb-brand-period"><i></i>Período: <b>' +
        safe_period + '</b></div></section>'
    )


def hero_banner(title, subtitle, players, matches, maps):
    """Safe HTML with truthful league metrics and a vector-like tactical motif."""
    chips = [("Jogadores", players), ("Partidas", matches), ("Mapas", maps)]
    rendered_chips = "".join(
        '<span class="edb-hero-chip"><b>' + _fmt(number) + '</b>' +
        label + '</span>' for label, number in chips
    )
    artwork = (
        '<div class="edb-hero-art" aria-hidden="true">'
        '<div class="edb-radar-grid"></div>'
        '<div class="edb-radar"><span class="edb-radar-axis-h"></span>'
        '<span class="edb-radar-axis-v"></span>'
        '<span class="edb-radar-dot a"></span><span class="edb-radar-dot b"></span>'
        '</div><span class="edb-radar-callout">TACTICAL / CS2</span></div>'
    )
    return (
        '<section class="hero edb-hero">'
        '<div class="edb-hero-copy"><span class="eyebrow">◆ EDB LEAGUE / CS2</span>'
        '<h1>' + escape(str(title)) + '</h1><p>' + escape(str(subtitle)) + '</p>'
        '<div class="edb-hero-chips">' + rendered_chips + '</div></div>' +
        artwork + '</section>'
    )
