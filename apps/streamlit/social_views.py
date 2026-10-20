"""Comparação lado a lado e vitrine das medalhas da EDB LEAGUE."""
from __future__ import annotations

from html import escape
from urllib.parse import quote
import pandas as pd
from chart_theme import style_edb_bar

SOCIAL_CSS = """
<style>
.edb-duel-grid{position:relative;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));
gap:14px;margin:15px 0}
.edb-duel-versus{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);
width:43px;height:43px;display:grid;place-items:center;border-radius:50%;z-index:2;
font-size:.76rem;font-weight:900;color:#F5F8FF;background:#0B1F36;
border:1px solid #5D9BD2;box-shadow:0 0 18px rgba(78,148,230,.27)}
.edb-duel-quick{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px;margin-top:16px;
padding-top:12px;border-top:1px solid rgba(162,194,225,.22)}
.edb-duel-quick span{display:block;color:#9FB8D0;font-size:.68rem}
.edb-duel-quick strong{display:block;color:#F1F8FD;font-size:.92rem;font-weight:850;margin-top:2px}
.edb-duel-player{border:1px solid #395873;border-radius:16px;
background:linear-gradient(135deg,#1C3652,#15263A);padding:17px;min-width:0}
.edb-duel-player--blue{border-color:#4E86B2;background:linear-gradient(135deg,#214B71,#172B43)}
/* O segundo jogador recebe vermelho mais marcante no cartão superior. */
.edb-duel-player--red{
 background:linear-gradient(135deg,#562938,#30202E);
 border:1px solid #AD5A69;
 box-shadow:inset 4px 0 0 #F07788,0 5px 18px rgba(92,26,45,.18);
}
.edb-duel-name{font-size:1.15rem;font-weight:850;overflow-wrap:anywhere}
.edb-duel-player--blue .edb-duel-name{color:#98D1FF}
.edb-duel-player--red .edb-duel-name{color:#FFA5B2}
.edb-duel-meta{color:#AFC4D8;font-size:.75rem;margin-top:6px}
.edb-duel-comparison{border:1px solid #39516B;border-radius:16px;
background:linear-gradient(135deg,#16283B,#111D2D);padding:10px 15px;margin:14px 0}
.edb-duel-metric{
 display:grid;grid-template-columns:minmax(0,1fr) minmax(90px,.55fr) minmax(90px,.55fr);
 gap:10px;align-items:stretch;border-bottom:1px solid #293E55;padding:0 3px;
}
.edb-duel-metric-label{
 display:flex;align-items:center;font-size:.85rem;color:#C0D1DF;padding:12px 0;
}
.edb-duel-value{
 display:flex;align-items:center;justify-content:flex-end;
 font-weight:800;font-variant-numeric:tabular-nums;font-size:1rem;
 color:#F0F5FB;text-align:right;min-width:0;padding:12px 0;
}
/* Divisória vertical contínua entre as colunas dos dois jogadores. */
.edb-duel-metric > .edb-duel-value:last-child{
 border-left:1px solid #5A7290;padding-left:12px;
}
.edb-duel-column-name{
 font-size:.88rem;line-height:1.3;
 font-weight:850;overflow-wrap:anywhere;
}
.edb-duel-column--blue{color:#98D1FF}
.edb-duel-column--red{color:#FF93A2}
.edb-duel-value-best{color:#D6B98A}
.edb-duel-note{color:#9FB5C8;font-size:.75rem;margin:12px 0}
.edb-medal-overview{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:14px 0 24px}
.edb-medal-overview-card{background:linear-gradient(125deg,#142F4A,#0B2238);border:1px solid #315676;
border-radius:12px;padding:14px;min-width:0}
.edb-medal-overview-card strong{font-size:1.45rem;color:#A3D2FF;font-weight:900;display:block}
.edb-medal-overview-card span{font-size:.73rem;color:#AFC8DC}
.edb-medal-tiers{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:12px 0 22px}
.edb-medal-tier-panel{border:1px solid #3B5067;border-radius:14px;padding:18px;
background:linear-gradient(125deg,#172B41,#0C1D2E)}
.edb-medal-tier-panel .name{font-weight:900;color:#F1F6FE;font-size:.97rem}
.edb-medal-tier-panel .sub{font-size:.76rem;color:#AFC3D5;margin-top:7px}
.edb-medal-tier-panel.bronze{border-color:#785648}
.edb-medal-tier-panel.silver{border-color:#687F97}
.edb-medal-tier-panel.gold{border-color:#97835B}
.edb-medal-tier-panel.gold .name{color:#E8C78E}
@media(max-width:700px){
 .edb-medal-overview{grid-template-columns:repeat(2,minmax(0,1fr))}
 .edb-medal-tiers{grid-template-columns:1fr;gap:8px}
}
.edb-medal-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));
gap:12px;margin:16px 0 24px}
.edb-medal-card{border:1px solid #3B4C63;border-radius:15px;
padding:15px 16px;background:#17283D;min-width:0}
.edb-medal-card.edb-unlocked{border-color:#8D7859;background:linear-gradient(135deg,#2B3446,#192B41)}
.edb-medal-title{color:#EDF5FB;font-size:.94rem;font-weight:850;overflow-wrap:anywhere}
.edb-medal-desc{color:#A8BDD0;font-size:.74rem;margin:6px 0 9px;line-height:1.5}
.edb-medal-meta{color:#B7C7D6;font-size:.7rem}
.edb-medal-tier{display:inline-block;min-width:65px;text-align:center;
border-radius:6px;padding:3px 8px;font-size:.66rem;font-weight:750;
letter-spacing:.5px;background:#283F5B;color:#DCE9F7}
.edb-tier-bronze{background:#4B382F;color:#E6B695}
.edb-tier-silver{background:#37495B;color:#D5E2EE}
.edb-tier-gold{background:#4B4131;color:#E8CB92}
.edb-medal-progress{height:6px;border-radius:10px;background:#273B53;
margin:10px 0 6px;overflow:hidden}
.edb-medal-progress>span{display:block;height:100%;
background:linear-gradient(90deg,#709CC8,#D6B98A);border-radius:10px}
.edb-medal-person a{color:#D8E9FA;text-decoration:none;
border-bottom:1px solid #6786A6}
.edb-medal-person a:hover{color:#FFFFFF;border-color:#D6B98A}
@media(max-width:650px){
 .edb-duel-grid,.edb-medal-grid{grid-template-columns:1fr}
 .edb-duel-player{padding:14px}
 .edb-duel-metric{grid-template-columns:minmax(0,1fr) minmax(64px,.62fr) minmax(64px,.62fr);gap:6px}
 .edb-duel-value{font-size:.91rem}
 .edb-duel-column-name{font-size:.73rem}
 .edb-duel-metric > .edb-duel-value:last-child{padding-left:7px}
 .edb-medal-card{padding:13px}
}
</style>
"""


def _fmt(value, decimals=0, suffix=""):
    if value is None or pd.isna(value):
        return "—"
    return f"{value:.{decimals}f}{suffix}"


def _link(pid, name):
    return ('<a href="?player=' + escape(quote(str(pid),safe=""),quote=True) +
            '" target="_self">' + escape(str(name)) + '</a>')


def render_compare(st, px, first, second, comparison):
    st.markdown(SOCIAL_CSS,unsafe_allow_html=True)
    fst, snd = comparison["first"], comparison["second"]
    names = []
    for player in (first, second):
        nickname = player.get("nickname") or "Jogador"
        real = (player.get("real_name") or "").strip()
        names.append(real if real and real.casefold()!=nickname.casefold() else nickname)
    st.markdown(
        '<div class="edb-duel-grid">' + "".join(
            '<section class="edb-duel-player edb-duel-player--' +
            ('blue' if index == 0 else 'red') +
            '"><div class="edb-duel-name">' + escape(name) +
            '</div><div class="edb-duel-meta">' +
            escape(f'Nick: {p.get("nickname") or ""}') +
            '</div><div class="edb-duel-quick">'
            '<div><span>Partidas</span><strong>' + str(info["games"]) + '</strong></div>'
            '<div><span>Vitórias</span><strong>' + str(info["wins"]) + '</strong></div>'
            '<div><span>Kills</span><strong>' + str(info["kills"]) + '</strong></div>'
            '</div></section>'
            for index,(name,p,info) in enumerate(zip(names,(first,second),(fst,snd)))
        )+'<div class="edb-duel-versus">VS</div></div>',unsafe_allow_html=True
    )

    metrics = [
        ("Partidas",fst["games"],snd["games"],0,""),
        ("Vitórias",fst["wins"],snd["wins"],0,""),
        ("Win rate",fst["win_rate"],snd["win_rate"],1,"%"),
        ("Kills",fst["kills"],snd["kills"],0,""),
        ("K/D",fst["kd"],snd["kd"],2,""),
        ("KPR",fst["kpr"],snd["kpr"],3,""),
        ("ADR estimado",fst["adr"],snd["adr"],1,""),
        ("Assistências",fst["assists"],snd["assists"],0,""),
    ]
    st.markdown("#### Comparação de carreira")
    markup=['<div class="edb-duel-comparison">']
    markup.append(
        '<div class="edb-duel-metric edb-duel-header">'
        '<div class="edb-duel-metric-label">Jogador</div>'
        '<div class="edb-duel-value edb-duel-column-name edb-duel-column--blue">' + escape(names[0]) + '</div>'
        '<div class="edb-duel-value edb-duel-column-name edb-duel-column--red">' + escape(names[1]) + '</div>'
        '</div>'
    )
    for title,a,b,dec,suffix in metrics:
        is_a = a is not None and b is not None and a > b
        is_b = a is not None and b is not None and b > a
        markup.append(
            '<div class="edb-duel-metric">'
            '<div class="edb-duel-metric-label">' + escape(title) + '</div>'
            '<div class="edb-duel-value' + (' edb-duel-value-best' if is_a else '') +
            '">' + _fmt(a,dec,suffix) + '</div>'
            '<div class="edb-duel-value' + (' edb-duel-value-best' if is_b else '') +
            '">' + _fmt(b,dec,suffix) + '</div></div>'
        )
    markup.append('</div>')
    st.markdown(''.join(markup),unsafe_allow_html=True)
    st.caption("Comparação de todas as partidas oficiais, sem limite semanal de XP. O ADR acumulado utiliza dano/rounds disponíveis.")

    st.markdown("#### Partidas em comum")
    shared=comparison["shared"]
    st.metric("Partidas em que os dois jogaram",comparison["shared_count"])
    if not shared:
        st.info("Eles ainda não disputaram nenhuma partida em comum. As estatísticas da carreira permanecem comparáveis.")
        return

    hc=comparison["head_to_head"]
    st.markdown(
        f'**Confrontos em lados opostos:** {comparison["opponent_games"]} · '
        f'**Vitórias:** {escape(names[0])} {hc[str(first["id"])]} × '
        f'{hc[str(second["id"])]} {escape(names[1])} · '
        f'**Companheiros de equipe:** {comparison["teammate_games"]}'
    )
    if comparison["opponent_games"] == 0:
        st.caption("Os jogadores só foram companheiros de equipe ou não há identificação confiável dos lados. Não existe confronto direto registrado.")
    rows=[]
    chart=[]
    for item in shared:
        x,y=item["first"],item["second"]
        label=f'{item["map"]} · {item["date"].strftime("%d/%m/%Y")}'
        rows.append({
            "Partida":label,"Relação":item["side"],
            f'Kills · {names[0]}':x["kills"],f'Kills · {names[1]}':y["kills"],
            f'ADR · {names[0]}':x["adr"],f'ADR · {names[1]}':y["adr"],
        })
        chart.extend([
            {"Partida":label,"Jogador":names[0],"Kills":x["kills"]},
            {"Partida":label,"Jogador":names[1],"Kills":y["kills"]},
        ])
    st.markdown("##### Eliminações por mapa")
    fig=px.bar(pd.DataFrame(chart),x="Partida",y="Kills",color="Jogador",barmode="group",
               text="Kills",color_discrete_sequence=["#78B8E8","#E28787"])
    style_edb_bar(fig,grouped=True)
    fig.update_traces(
        texttemplate="%{y:.0f}",
        hovertemplate="Mapa: %{x}<br>Kills: %{y}<extra>%{fullData.name}</extra>"
    )
    fig.update_layout(
        height=max(325,80*len(shared)+180),
        xaxis_title="",yaxis_title="Kills",
        legend_title_text="",legend=dict(
            orientation="h",yanchor="bottom",y=1.03,xanchor="left",x=0
        ),
        margin=dict(l=12,r=20,t=48,b=72)
    )
    fig.update_xaxes(tickangle=-22)
    st.plotly_chart(fig,use_container_width=True)
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
    st.caption("Vitória em confronto direto é vitória da equipe, não abates de um jogador contra o outro.")


def render_achievement_collection(st, medals):
    st.markdown(SOCIAL_CSS,unsafe_allow_html=True)
    earned=[m for m in medals if m["earned"]]
    locked=[m for m in medals if not m["earned"]]
    st.caption(f'{len(earned)} de {len(medals)} medalhas conquistadas')
    for heading,rows in (("Conquistadas",earned),("Próximos desafios",locked)):
        st.markdown("##### "+heading)
        if not rows:
            st.caption("Nenhuma medalha nesta categoria.")
            continue
        markup=['<div class="edb-medal-grid">']
        for m in rows:
            progress=m["progress"]
            progress_html=(
                '<div class="edb-medal-progress"><span style="width:' +
                str(progress) + '%"></span></div><div class="edb-medal-meta">' +
                str(m["current"]) + " / " + str(m["target"]) + "</div>"
                if progress is not None else
                '<div class="edb-medal-meta">Sem dados disponíveis para esta métrica</div>'
            )
            markup.append(
                '<article class="edb-medal-card' + (' edb-unlocked' if m["earned"] else '') + '">'
                '<span class="edb-medal-tier edb-tier-' + escape(m["tier"]) + '">' +
                escape({"bronze":"BRONZE","silver":"PRATA","gold":"OURO"}[m["tier"]]) + '</span>'
                '<div class="edb-medal-title">' + escape(m["name"]) + '</div>'
                '<div class="edb-medal-desc">' + escape(m["description"]) + '</div>' +
                progress_html + '</article>'
            )
        st.markdown(''.join(markup)+'</div>',unsafe_allow_html=True)


def render_medal_catalogue(st, players, medals_by_id):
    """Painel de conquistas oficiais, sem simular medalhas ou vencedores."""
    from league_social import MEDALS
    st.markdown(SOCIAL_CSS,unsafe_allow_html=True)
    types = len(MEDALS)
    earned = [m for medals in medals_by_id.values() for m in medals if m["earned"]]
    honored = sum(
        any(m["earned"] for m in medals_by_id.get(str(p["id"]),[]))
        for p in players
    )
    summary = [
        ("Medalhas disponíveis", types),
        ("Jogadores premiados", honored),
        ("Níveis de conquista", 3),
        ("Medalhas conquistadas", len(earned)),
    ]
    st.markdown('<div class="edb-medal-overview">' + "".join(
        '<div class="edb-medal-overview-card"><strong>' +
        str(value) + '</strong><span>' + escape(label) + '</span></div>'
        for label,value in summary
    ) + '</div>',unsafe_allow_html=True)
    st.markdown('### Categorias de medalhas')
    captions = {"bronze": "Os primeiros marcos da jornada.",
                "silver": "Constância e destaque nas partidas.",
                "gold": "Feitos raros que merecem reconhecimento."}
    tiers = [("bronze","Bronze"),("silver","Prata"),("gold","Ouro")]
    tiles = []
    for tier,label in tiers:
        count = sum(m["tier"] == tier for m in MEDALS)
        tiles.append(
            '<div class="edb-medal-tier-panel ' + tier + '">'
            '<div class="name">' + label + '</div>'
            '<div class="sub">' + str(count) + ' medalhas · ' +
            captions[tier] + '</div></div>'
        )
    st.markdown('<div class="edb-medal-tiers">' + ''.join(tiles) + '</div>',
                unsafe_allow_html=True)
    st.markdown('### Medalhas da EDB LEAGUE')
    st.caption("Vencedores vinculados ao cadastro dos jogadores. Todos os números refletem partidas registradas.")
    markup=['<div class="edb-medal-grid">']
    for m in MEDALS:
        holders=[]
        for player in players:
            awarded=medals_by_id.get(str(player["id"]),[])
            if any(x["id"]==m["id"] and x["earned"] for x in awarded):
                nick=player.get("nickname") or "Jogador"
                real=(player.get("real_name") or "").strip()
                name=f"{real} ({nick})" if real and real.casefold()!=nick.casefold() else nick
                holders.append(_link(player["id"],name))
        markup.append(
            '<article class="edb-medal-card' + (' edb-unlocked' if holders else '') + '">'
            '<span class="edb-medal-tier edb-tier-' + escape(m["tier"]) + '">' +
            escape({"bronze":"BRONZE","silver":"PRATA","gold":"OURO"}[m["tier"]]) + '</span>'
            '<div class="edb-medal-title">' + escape(m["name"]) + '</div>'
            '<div class="edb-medal-desc">' + escape(m["description"]) + '</div>'
            '<div class="edb-medal-meta">' + str(len(holders)) +
            (' jogadores conquistaram' if len(holders)!=1 else ' jogador conquistou') + '</div>'
            '<div class="edb-medal-person">' + ' · '.join(holders[:8]) +
            (" · …" if len(holders)>8 else "") + '</div>'
            '</article>'
        )
    st.markdown(''.join(markup)+'</div>',unsafe_allow_html=True)
    st.caption("Abra o perfil de um jogador para ver as medalhas conquistadas e seu progresso individual.")
