"""Navegação horizontal responsiva e acesso administrativo fixo da EDB LEAGUE."""
from __future__ import annotations

from html import escape
from pathlib import Path
from functools import lru_cache

NAV_ITEMS = (
    ("home", "Visão geral", ""),
    ("rankings", "Rankings", "Rankings"),
    ("matches", "Partidas", "Partidas"),
    ("versus", "Comparar jogadores", "Comparar jogadores"),
    ("fame", "Hall da Fama", "Hall da Fama"),
    ("medals", "Medalhas", "Medalhas"),
    ("xp", "Missões & XP", "Missões & XP"),
)
EXTRA_ROUTES = {"players": "Jogadores", "admin": "Administração"}
ROUTES = {slug: page for slug, page, _ in NAV_ITEMS} | EXTRA_ROUTES

HOME_SVG = (
    '<svg viewBox="0 0 24 24" width="20" height="20" '
    'fill="none" stroke="currentColor" stroke-width="2" '
    'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1V10Z"/>'
    '</svg>'
)
LOCK_SVG = (
    '<svg viewBox="0 0 24 24" width="16" height="16" '
    'fill="none" stroke="currentColor" stroke-width="2" '
    'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<rect x="5" y="10" width="14" height="11" rx="2"/>'
    '<path d="M8 10V7a4 4 0 0 1 8 0v3"/>'
    '</svg>'
)

TOP_NAV_CSS = """
<style>
/* A marca e as categorias dividem o mesmo cabeçalho junto ao topo. */
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] {
  display:none !important;
}
[data-testid="stHeader"], [data-testid="stToolbar"], #MainMenu {
  display:none !important;
}
.block-container {padding-top:0.25rem !important;padding-bottom:5.5rem !important;}
.edb-topbar {
  display:flex;align-items:center;gap:20px;
  min-height:66px;padding:5px 15px 5px 13px;margin:0 0 12px;
  background:#08182B;
  border:1px solid #243B55;border-radius:11px;
  box-shadow:0 7px 22px rgba(0,0,0,.14);
  position:relative;isolation:isolate;
}
.edb-topbrand {
  display:inline-flex;align-items:center;gap:9px;
  color:#F2F6FD !important;text-decoration:none !important;
  flex:0 0 auto;white-space:nowrap;min-width:0;
}
.edb-topbrand img {
  width:48px;height:48px;object-fit:contain;display:block;
  filter:drop-shadow(0 1px 4px rgba(209,170,107,.12));
}
.edb-topbrand-name {
  font-size:.95rem;font-weight:900;letter-spacing:.9px;
  color:#F4F7FC;line-height:1;
}
.edb-topnav {
  display:flex;align-items:stretch;justify-content:flex-end;
  gap:4px;flex:1 1 auto;min-width:0;
  height:55px;margin:0;padding:0 2px;
  overflow-x:auto;overscroll-behavior-inline:contain;
  scrollbar-width:none;-webkit-overflow-scrolling:touch;
}
.edb-topnav::-webkit-scrollbar {display:none;}
.edb-topnav a {
  position:relative;display:inline-flex;align-items:center;justify-content:center;
  flex:0 0 auto;white-space:nowrap;padding:10px 13px 12px;
  font-size:.78rem;font-weight:680;line-height:1.3;
  color:#A8BCD2 !important;text-decoration:none !important;
  border:none;border-radius:0;min-height:50px;
  background:transparent;
  transition:color .15s,background .15s;
}
.edb-topnav a:hover,.edb-topnav a:focus-visible {
  color:#EBF6FF !important;background:rgba(77,134,193,.10);
}
.edb-topnav a.edb-nav-selected {
  color:#91D4FF !important;font-weight:850;
  background:transparent;
}
.edb-topnav a.edb-nav-selected:after {
  content:"";position:absolute;bottom:1px;left:17%;right:17%;
  height:3px;border-radius:4px;
  background:#65C4FC;box-shadow:0 0 9px rgba(101,196,252,.5);
}
.edb-topnav .edb-nav-home {min-width:46px;padding:10px 13px;}
.edb-nav-home svg {display:block;}
/* Informações reais continuam acessíveis depois do cabeçalho. */
.edb-topmeta {display:flex;align-items:center;gap:13px;flex-wrap:wrap;
  min-height:35px;color:#A3BFD9;font-size:.78rem;padding:2px 2px 6px;}
.edb-topmeta b {color:#E7D0AA;font-variant-numeric:tabular-nums;font-weight:850;}
/* Acesso administrativo permanece separado, fixo no canto inferior esquerdo. */
.edb-admin-float {
  position:fixed;left:18px;bottom:18px;z-index:999;
  display:inline-flex;align-items:center;gap:8px;
  min-height:43px;padding:10px 15px;border-radius:12px;
  color:#C9DDEE !important;text-decoration:none !important;
  background:linear-gradient(135deg,#152D45,#0F2236);
  border:1px solid #486D8F;box-shadow:0 7px 23px rgba(0,0,0,.42);
  font-size:.78rem;font-weight:750;
}
.edb-admin-float:hover,.edb-admin-float:focus-visible {
  border-color:#83BCEB;color:#FFFFFF !important;background:#284B6A;
}
.edb-admin-float.edb-admin-selected {
  color:#EBCF9F !important;border-color:#9D8460;
}
@media(max-width:1080px) {
  .edb-topbar {gap:12px;padding:4px 10px;min-height:59px;}
  .edb-topbrand img {width:42px;height:42px;}
  .edb-topbrand-name {font-size:.85rem;letter-spacing:.55px;}
  .edb-topnav {justify-content:flex-start;height:51px;}
  .edb-topnav a {font-size:.75rem;padding:8px 10px 11px;}
}
@media(max-width:650px) {
  .block-container {padding-top:0.1rem !important;}
  .edb-topbar {gap:8px;min-height:54px;padding:4px 7px;margin-bottom:8px;border-radius:9px;}
  .edb-topbrand {gap:4px;}
  .edb-topbrand img {width:36px;height:36px;}
  .edb-topbrand-name {font-size:.72rem;letter-spacing:0;}
  .edb-topnav {height:46px;scroll-snap-type:x proximity;}
  .edb-topnav a {scroll-snap-align:start;min-height:42px;font-size:.73rem;padding:8px 10px;}
  .edb-admin-float {left:11px;bottom:12px;min-height:40px;padding:9px 11px;font-size:.73rem;}
  .edb-topmeta {font-size:.7rem;gap:9px;}
}
</style>
"""


@lru_cache(maxsize=1)
def _crest_image():
    """Imagem fornecida pelo usuário, otimizada e armazenada no próprio repositório."""
    path = Path(__file__).resolve().parent / "assets" / "edb_crest.webp.b64"
    try:
        return path.read_text(encoding="ascii").strip()
    except OSError:
        return ""


def top_navigation(page):
    """Links internos acessíveis: o usuário navega sem botão do Streamlit na sidebar."""
    links = []
    for slug, destination, label in NAV_ITEMS:
        active = destination == page
        selected = ' edb-nav-selected' if active else ''
        icon_class = ' edb-nav-home' if slug == "home" else ''
        visible = HOME_SVG if slug == "home" else escape(label)
        links.append(
            '<a href="?page=' + slug + '" target="_self"'
            ' class="edb-nav-item' + selected + icon_class + '"'
            ' aria-label="' + escape(destination, quote=True) + '"'
            ' aria-current="' + ('page' if active else 'false') + '">'
            + visible + '</a>'
        )
    admin_class = ' edb-admin-selected' if page == "Administração" else ''
    admin = (
        '<a class="edb-admin-float' + admin_class + '"'
        ' href="?page=admin" target="_self" aria-label="Administrador">'
        + LOCK_SVG + 'Administrador</a>'
    )
    image = _crest_image()
    logo = ('<img src="data:image/webp;base64,' + image +
            '" alt="Brasão EDB LEAGUE" width="48" height="48" />'
            if image else '<span aria-hidden="true">EDB</span>')
    brand = ('<a class="edb-topbrand" href="?page=home" target="_self"'
             ' aria-label="EDB LEAGUE, página inicial">' +
             logo + '<span class="edb-topbrand-name">EDB LEAGUE</span></a>')
    return ('<header class="edb-topbar">' + brand +
            '<nav class="edb-topnav" aria-label="Categorias da EDB LEAGUE">' +
            ''.join(links) + '</nav></header>' + admin)


def top_counters(players, matches, kills):
    """Resumo factual sem precisar abrir o menu lateral."""
    return (
        '<div class="edb-topmeta"><span><b>' + str(int(players)) +
        '</b> jogadores</span><span><b>' + str(int(matches)) +
        '</b> partidas</span><span><b>' + str(int(kills)) +
        '</b> kills registradas</span></div>'
    )
