"""Views for player profiles and Hall of Fame in EDB LEAGUE."""
from __future__ import annotations

from html import escape
from urllib.parse import quote
import pandas as pd

LEGACY_CSS = """
<style>
.edb-profile-head{border:1px solid #365773;border-radius:18px;padding:20px;
background:linear-gradient(115deg,#1D3751,#14263A);margin:14px 0}
.edb-profile-name{font-size:clamp(1.3rem,4vw,1.8rem);font-weight:850;color:#F3F8FE}
.edb-profile-meta{font-size:.82rem;color:#B5CCE0;margin-top:7px}
.edb-profile-stars{color:#D6B98A;letter-spacing:2px}
.edb-profile-metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));
gap:10px;margin:15px 0 22px}
.edb-profile-metric{background:#15283C;border:1px solid #2F465E;
border-radius:13px;padding:14px}
.edb-profile-metric-label{color:#9DB5CB;font-size:.72rem}
.edb-profile-metric-value{color:#EFF6FD;font-size:1.3rem;font-weight:850;margin-top:3px}
.edb-profile-best{border-left:3px solid #D6B98A;background:#1F3042;
padding:14px;border-radius:9px;color:#F3F1EA;margin:14px 0}
.edb-fame-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin:16px 0}
.edb-fame-card{border:1px solid #354A60;border-radius:16px;
background:linear-gradient(140deg,#1B2E43,#142235);padding:18px;min-width:0}
.edb-fame-card:first-child{border-color:#806C50}
.edb-fame-title{font-size:.76rem;color:#A9BECE;letter-spacing:.5px;font-weight:750}
.edb-fame-score{font-size:1.5rem;color:#D6B98A;font-weight:850;margin:8px 0}
.edb-fame-people{font-size:.93rem;font-weight:700;color:#EFF4FA;overflow-wrap:anywhere}
.edb-fame-people a{color:#CCE4F8;text-decoration:none;border-bottom:1px solid #4C7291}
.edb-fame-people a:hover{color:#FFFFFF;border-color:#D6B98A}
.edb-fame-detail{font-size:.73rem;color:#9DB3C6;margin-top:9px}
.edb-profile-badges{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0 16px}
.edb-profile-badge{background:#273448;color:#E4D0AB;border:1px solid #6A604E;
border-radius:30px;padding:7px 12px;font-size:.75rem;font-weight:700}
@media(max-width:630px){
 .edb-profile-head{padding:15px}
 .edb-profile-metrics{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
 .edb-profile-metric{padding:12px}
 .edb-profile-metric-value{font-size:1.14rem}
 .edb-fame-grid{grid-template-columns:1fr}
 .edb-fame-card{padding:15px}
}
</style>
"""


def _fmt(value, places=0, suffix=""):
    if value is None or pd.isna(value):
        return "—"
    return f"{value:.{places}f}{suffix}"


def profile_link(player_id):
    return "?player=" + quote(str(player_id), safe="")


def render_profile(st, px, player, data, hall):
    """Full career view based on all recorded matches, never the weekly XP cap."""
    label = str(player.get("real_name") or "").strip()
    nick = str(player.get("nickname") or "Jogador")
    name = label if label and label.casefold() != nick.casefold() else nick
    extra = " · ".join([part for part in [f"Nick oficial: {nick}", "Visitante" if player.get("is_guest") else "Integrante"] if part])
    stars = max(1, min(5, int(player.get("stars") or 3)))
    info = " · Perfil provisório" if data["games"] < 2 else ""
    st.markdown(LEGACY_CSS, unsafe_allow_html=True)
    st.markdown(
        '<section class="edb-profile-head"><div class="edb-profile-name">' +
        escape(name) + '</div><div class="edb-profile-meta">' + escape(extra) +
        ' · <span class="edb-profile-stars">' + ("★" * stars) + "</span>" +
        escape(info) + "</div></section>", unsafe_allow_html=True
    )
    metrics = [
        ("Partidas", str(data["games"])), ("Vitórias", str(data["wins"])),
        ("Win rate", _fmt(data["win_rate"],1,"%")),
        ("Kills", str(data["kills"])), ("K/D", _fmt(data["kd"],2)),
        ("KPR", _fmt(data["kpr"],3)), ("ADR estimado", _fmt(data["adr"],1)),
        ("Assistências", str(data["assists"])),
    ]
    st.markdown('<div class="edb-profile-metrics">' + "".join(
        '<div class="edb-profile-metric"><div class="edb-profile-metric-label">' +
        escape(title) + '</div><div class="edb-profile-metric-value">' + escape(value) +
        '</div></div>' for title,value in metrics
    ) + '</div>', unsafe_allow_html=True)

    if data["games"] == 0:
        st.info("Ainda não há partidas registradas para este jogador.")
        return
    best = data["best"]
    if best:
        st.markdown(
            '<div class="edb-profile-best">Melhor marca de eliminações: <strong>' +
            str(best["kills"]) + " kills</strong> em " +
            escape(str(best["map"])) + " · " + best["date"].strftime("%d/%m/%Y") +
            "</div>", unsafe_allow_html=True
        )
    awards = [entry["title"] for entry in hall if any(h["id"] == str(player["id"]) for h in entry["holders"])]
    badges = []
    if data["wins"] >= 1: badges.append("Primeira vitória")
    if any(r["kills"] >= 20 for r in data["matches"]): badges.append("20 kills em uma partida")
    if data["kills"] >= 50: badges.append("50 kills na liga")
    if data["kills"] >= 100: badges.append("100 kills na liga")
    if awards: badges.extend("Recorde: " + title for title in awards)
    if badges:
        st.markdown("#### Conquistas e recordes")
        st.markdown('<div class="edb-profile-badges">' + "".join(
            '<span class="edb-profile-badge">' + escape(x) + '</span>' for x in badges
        ) + '</div>', unsafe_allow_html=True)
    st.caption("Conquistas calculadas automaticamente a partir das partidas registradas.")

    st.markdown("#### Evolução de desempenho")
    timeline = pd.DataFrame([{
        "Partida": f"{r['map']} · {r['date'].strftime('%d/%m')}",
        "KPR": r["kpr"], "ADR": r["adr"], "Kills": r["kills"]
    } for r in data["matches"]])
    tabs = st.tabs(["KPR por partida", "ADR por partida"])
    for metric, tab in zip(("KPR", "ADR"), tabs):
        with tab:
            if timeline[metric].notna().any():
                fig = px.line(timeline, x="Partida", y=metric, markers=True,
                              color_discrete_sequence=["#78B8E8"])
                fig.update_layout(height=285, paper_bgcolor="rgba(0,0,0,0)",
                                  plot_bgcolor="rgba(0,0,0,0)", font_color="#C3D7E8",
                                  margin=dict(l=5,r=10,t=15,b=25),
                                  xaxis_title="", yaxis_title=metric)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Ainda não há dados para esta métrica.")

    st.markdown("#### Histórico de partidas")
    history = pd.DataFrame([{
        "Data": r["date"].strftime("%d/%m/%Y"),
        "Mapa": r["map"], "Nick usado": r["played_nick"],
        "Resultado": "Vitória" if r["won"] is True else "Derrota" if r["won"] is False else "—",
        "K": r["kills"], "D": r["deaths"], "A": r["assists"],
        "K/D": round(r["kd"],2) if r["kd"] is not None else None,
        "ADR": round(r["adr"],1) if r["adr"] is not None else None,
        "Rating": round(r["rating"],2) if r["rating"] is not None else None,
    } for r in reversed(data["matches"])])
    st.dataframe(history, hide_index=True, use_container_width=True)
    st.caption("Os totais usam todas as partidas. O ADR acumulado é calculado por dano/rounds; partidas com rounds estimados podem afetá-lo.")


def render_hall(st, hall, matches_count):
    st.markdown(LEGACY_CSS, unsafe_allow_html=True)
    st.caption(f"Recordes automáticos de {matches_count} partidas oficiais. Empates são compartilhados.")
    if not hall:
        st.info("Ainda não há estatísticas suficientes para estabelecer recordes.")
        return
    markup = ['<div class="edb-fame-grid">']
    for entry in hall:
        names = " · ".join(
            '<a href="' + escape(profile_link(h["id"]),quote=True) +
            '" target="_self">' + escape(h["name"]) + '</a>' for h in entry["holders"]
        )
        markup.append(
            '<article class="edb-fame-card">'
            '<div class="edb-fame-title">' + escape(entry["title"]) + '</div>'
            '<div class="edb-fame-score">' + escape(entry["value"]) + '</div>'
            '<div class="edb-fame-people">' + names + '</div>'
            '<div class="edb-fame-detail">' + escape(entry["detail"]) + '</div>'
            '</article>'
        )
    markup.append("</div>")
    st.markdown("".join(markup),unsafe_allow_html=True)
    st.caption("Recordes individuais consideram todas as partidas e os dados disponíveis no SCOPE.GG. K/D geral exige ao menos duas partidas.")
