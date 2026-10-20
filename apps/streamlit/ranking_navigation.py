"""Navegação angular independente do mecanismo de abas do Streamlit.

Links na mesma página mudam ?ranking=, preservando o backend e os dados.
"""
from __future__ import annotations

from html import escape

RANK_OPTIONS = (
    ("elite", "Elite"),
    ("superacao", "Superação"),
    ("resenha", "BAGRES"),
)

RANK_SWITCH_CSS = """
<style>
.edb-rank-switch{
  display:grid;grid-template-columns:repeat(3,minmax(0,1fr));
  gap:10px;max-width:790px;margin:14px 0 22px;
}
.edb-rank-switch a.edb-rank-option{
  display:flex;align-items:center;justify-content:center;min-height:59px;
  padding:13px 20px;color:#D1DEEB !important;text-decoration:none !important;
  text-align:center;font-size:.9rem;font-weight:800;letter-spacing:.055em;
  text-transform:uppercase;line-height:1.2;white-space:nowrap;
  border:0;border-radius:0;
  clip-path:polygon(12px 0,calc(100% - 12px) 0,100% 50%,
                    calc(100% - 12px) 100%,12px 100%,0 50%);
  background:linear-gradient(125deg,#203B56 0%,#13293D 100%);
  transition:background .15s ease,color .15s ease;
  box-sizing:border-box;
}
.edb-rank-switch a.edb-rank-option:hover,
.edb-rank-switch a.edb-rank-option:focus-visible{
  color:#fff !important;background:linear-gradient(125deg,#315E82,#203D57);
  outline-offset:2px;
}
.edb-rank-switch a.edb-rank-option.edb-rank-option--active{
  background:linear-gradient(120deg,#34749F 0%,#225477 100%);
  color:#fff !important;
  box-shadow:inset 0 -4px #87D6FF;
}
@media(max-width:650px){
  .edb-rank-switch{gap:5px;}
  .edb-rank-switch a.edb-rank-option{
    min-height:47px;padding:10px 5px;font-size:.70rem;letter-spacing:.01em;
    clip-path:polygon(7px 0,calc(100% - 7px) 0,100% 50%,
                      calc(100% - 7px) 100%,7px 100%,0 50%);
  }
}
</style>
"""


def rank_switch(selected: str, season=None) -> str:
    """Renderiza links angulares reais, sem <button> nem st.tabs."""
    if selected not in {slug for slug, _ in RANK_OPTIONS}:
        selected = "elite"
    out = [RANK_SWITCH_CSS, '<nav class="edb-rank-switch" aria-label="Categorias dos rankings">']
    for slug, label in RANK_OPTIONS:
        active = slug == selected
        cls = ' edb-rank-option--active' if active else ''
        # Fallback inline para manter o formato mesmo se o CSS global do
        # Streamlit sobrescrever classes ou mudar o DOM interno.
        background = (
            'linear-gradient(120deg,#34749F,#225477)'
            if active else 'linear-gradient(125deg,#203B56,#13293D)'
        )
        shadow = 'box-shadow:inset 0 -4px #87D6FF;' if active else ''
        inline = (
            'display:flex;align-items:center;justify-content:center;'
            'min-height:59px;padding:13px 20px;'
            'clip-path:polygon(12px 0,calc(100% - 12px) 0,100% 50%,'
            'calc(100% - 12px) 100%,12px 100%,0 50%);'
            'border-radius:0;border:0;text-decoration:none;'
            f'background:{background};color:{"#fff" if active else "#D1DEEB"};'
            f'{shadow}'
        )
        link='?page=rankings&amp;ranking=' + slug
        if season is not None:
            link+='&amp;season='+str(int(season))
        out.append(
            '<a class="edb-rank-option' + cls + '"'
            ' href="' + link + '" target="_self"'
            ' aria-label="Ranking ' + escape(label, quote=True) + '"'
            ' aria-current="' + ('page' if active else 'false') + '"'
            ' style="' + inline + '">' + escape(label) + '</a>'
        )
    out.append('</nav>')
    return ''.join(out)
