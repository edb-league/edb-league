"""Visual dos dois banners da aba Administração (cadastrar e configurar jogador)."""
from __future__ import annotations

from html import escape

ADMIN_CSS = """
<style>
/* Dois banners lado a lado, com a mesma altura mínima e a estética dos painéis do site. */
.st-key-edb_admin_register,.st-key-edb_admin_config{
  box-sizing:border-box;min-height:520px;padding:24px 24px 20px;
  border:1px solid #365A79;border-radius:20px;
  box-shadow:0 12px 28px rgba(0,0,0,.20);
  background:radial-gradient(ellipse at 95% 0%,rgba(85,146,201,.16),transparent 50%),
             linear-gradient(145deg,#142D45 0%,#102237 60%,#0D1B2B 100%);
}
.st-key-edb_admin_config{
  border-color:#796548;
  background:radial-gradient(ellipse at 95% 0%,rgba(214,185,138,.13),transparent 50%),
             linear-gradient(145deg,#192C40 0%,#102237 60%,#0D1B2B 100%);
}
.edb-admin-kicker{font-size:.7rem;letter-spacing:1.5px;font-weight:850;color:#8FCBF3;}
.st-key-edb_admin_config .edb-admin-kicker{color:#E8C893;}
.edb-admin-title{font-size:1.5rem;font-weight:900;color:#EEF6FF;margin:6px 0 3px;}
.edb-admin-sub{font-size:.8rem;color:#9FB6CA;margin-bottom:10px;line-height:1.45;}
.st-key-edb_admin_register [data-testid="stForm"]{
  border:none;padding:0;background:transparent;
}
.st-key-edb_admin_config [data-testid="stForm"]{
  border:1px solid rgba(135,170,205,.20);border-radius:14px;
  background:rgba(8,20,34,.38);padding:14px 16px;
}
@media(max-width:700px){
  .st-key-edb_admin_register,.st-key-edb_admin_config{min-height:0;padding:18px 16px 16px;}
}
</style>
"""


def admin_banner_head(kicker, title, subtitle, with_css=False):
    """Cabeçalho do banner; o CSS acompanha o primeiro, evitando bloco vazio."""
    return (
        (ADMIN_CSS if with_css else "") +
        '<div class="edb-admin-kicker">' + escape(kicker) + '</div>'
        '<div class="edb-admin-title">' + escape(title) + '</div>'
        '<div class="edb-admin-sub">' + escape(subtitle) + '</div>'
    )
