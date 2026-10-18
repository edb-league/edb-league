"""Navegação horizontal responsiva e acesso administrativo fixo da EDB LEAGUE."""
from __future__ import annotations

from html import escape

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
/* Barra de categorias: ocupa o topo, sem depender de menu lateral. */
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] {
  display:none !important;
}
[data-testid="stHeader"], [data-testid="stToolbar"], #MainMenu {
  display:none !important;
}
.block-container {padding-top:.7rem !important;padding-bottom:5.5rem !important;}
.edb-topnav {
  display:flex;align-items:center;gap:6px;padding:8px 10px;
  margin-bottom:11px;border:1px solid #335575;border-radius:17px;
  background:linear-gradient(120deg,#122B46,#0B1F33);
  box-shadow:0 12px 28px rgba(0,0,0,.17);
  overflow-x:auto;overscroll-behavior-inline:contain;
  scrollbar-width:thin;scrollbar-color:#48769B transparent;
  -webkit-overflow-scrolling:touch;
}
.edb-topnav a {
  display:inline-flex;align-items:center;justify-content:center;gap:7px;
  flex:0 0 auto;min-height:40px;white-space:nowrap;
  padding:9px 12px;border:1px solid transparent;border-radius:11px;
  font-size:.82rem;font-weight:750;line-height:1.2;
  color:#BBD0E4 !important;text-decoration:none !important;
  transition:background .15s,border-color .15s,color .15s;
}
.edb-topnav a:hover, .edb-topnav a:focus-visible {
  background:#24405D;border-color:#456D92;color:#FFFFFF !important;
}
.edb-topnav a.edb-nav-selected {
  background:linear-gradient(135deg,#28547B,#234565);
  border-color:#5B93C4;color:#F5FAFF !important;
  box-shadow:inset 0 -3px #8BC7F4;
}
.edb-topnav .edb-nav-home {min-width:44px;padding:8px 11px;}
.edb-nav-home svg {display:block;}
/* O período e os contadores continuam acessíveis no conteúdo principal. */
.edb-topmeta {display:flex;align-items:center;gap:13px;flex-wrap:wrap;
  min-height:40px;color:#A3BFD9;font-size:.78rem;padding:2px 2px 7px;}
.edb-topmeta b {color:#E7D0AA;font-variant-numeric:tabular-nums;font-weight:850;}
/* Admin fica isolado das categorias, sempre no canto inferior esquerdo. */
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
@media(max-width:850px) {
  .edb-topnav {border-radius:14px;gap:4px;padding:7px;margin-bottom:10px;}
  .edb-topnav a {font-size:.78rem;padding:8px 10px;}
}
@media(max-width:650px) {
  .edb-topnav {margin-right:-6px;border-radius:13px;scroll-snap-type:x proximity;}
  .edb-topnav a {scroll-snap-align:start;min-height:42px;}
  .edb-admin-float {left:11px;bottom:12px;min-height:40px;padding:9px 11px;font-size:.73rem;}
  .edb-topmeta {font-size:.7rem;gap:9px;}
}
</style>
"""


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
    return ('<nav class="edb-topnav" aria-label="Categorias da EDB LEAGUE">'
            + ''.join(links) + '</nav>' + admin)


def top_counters(players, matches, kills):
    """Resumo factual sem precisar abrir o menu lateral."""
    return (
        '<div class="edb-topmeta"><span><b>' + str(int(players)) +
        '</b> jogadores</span><span><b>' + str(int(matches)) +
        '</b> partidas</span><span><b>' + str(int(kills)) +
        '</b> kills registradas</span></div>'
    )
