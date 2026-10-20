"""Painel administrativo para registrar séries BO1 e BO3 de forma auditável."""
from __future__ import annotations

from confront_registry import prepare_confront_bundle


def render_confront_admin(st, store, seasons, matches, stats, players,
                         linked_maps, clear_cache, name_formatter):
    st.markdown("#### Registrar confronto BO1 ou BO3")
    st.caption(
        "Primeiro importe os mapas com seus dados na aba Importar demo / CSV. "
        "Aqui você escolhe 1 mapa (BO1) ou 3 mapas (BO3), informa os placares "
        "e confirma os dois times. Cada mapa conta igualmente nos rankings."
    )
    if not store.cloud:
        st.info("O registro oficial de confrontos exige Supabase.")
        return

    available_seasons=[
        s for s in seasons if int(s["number"])>=1 and
        not s.get("homologated_at") and s.get("starts_on") and s.get("ends_on")
    ]
    if not available_seasons:
        st.info("Não há temporadas abertas para registrar confrontos.")
        return
    season=st.selectbox(
        "Temporada",
        sorted(available_seasons,key=lambda x:int(x["number"]),reverse=True),
        format_func=lambda x:x["label"],key="edb_confront_season"
    )
    chosen_format=st.radio(
        "Formato da partida",["BO1","BO3"],
        horizontal=True,key="edb_confront_format"
    )
    total=1 if chosen_format=="BO1" else 3
    linked={str(row["match_id"]) for row in linked_maps}
    candidates=[
        m for m in matches if str(m["id"]) not in linked and
        str(season["starts_on"])[:10] <= str(m["played_at"])[:10] <=
        str(season["ends_on"])[:10]
    ]
    by_match={str(m["id"]):m for m in candidates}
    chosen=st.multiselect(
        f"Selecione {total} mapa(s), na ordem em que foram disputados",
        list(by_match),
        format_func=lambda mid:(
            str(by_match[mid].get("played_at"))[:10]+" · "+
            str(by_match[mid].get("map_name") or "Mapa")+" · "+mid[:12]
        ),
        max_selections=total,key="edb_confront_maps"
    )
    if not candidates:
        st.info("Nenhum mapa avulso disponível nesta temporada. Importe o primeiro mapa.")
        return
    if len(chosen)!=total:
        st.info(f"Selecione exatamente {total} mapa(s) para continuar.")
        return

    roster=sorted({
        str(row["player_id"]) for row in stats
        if str(row["match_id"])==chosen[0]
    })
    by_player={str(p["id"]):p for p in players}
    if len(roster)!=10 or any(pid not in by_player for pid in roster):
        st.error("O primeiro mapa deve ter 10 jogadores cadastrados, 5 contra 5.")
        return
    left,right=st.columns(2)
    with left:
        team_a=st.text_input("Time A (vermelho)",value="PT",key="edb_confront_a_name")
    with right:
        team_b=st.text_input("Time B (azul)",value="PL",key="edb_confront_b_name")
    selected_a=st.multiselect(
        "Escolha os 5 jogadores do Time A",
        roster,max_selections=5,key="edb_confront_team_a_players",
        format_func=lambda pid:name_formatter(by_player[pid]["nickname"])
    )
    if len(selected_a)==5:
        st.caption(
            "Time B: "+", ".join(name_formatter(by_player[pid]["nickname"])
                                for pid in roster if pid not in selected_a)
        )

    scores={}
    for index,mid in enumerate(chosen,1):
        m=by_match[mid]
        st.markdown(
            f"**Mapa {index} · {m.get('map_name') or 'Mapa'}** "
            f"({str(m.get('played_at'))[:10]})"
        )
        a_col,b_col=st.columns(2)
        with a_col:
            a_score=st.number_input(
                f"Rounds do {team_a or 'Time A'} · mapa {index}",
                min_value=0,max_value=80,step=1,
                value=int(m.get("team_a_score") or 0),
                key="edb_confront_score_a_"+mid
            )
        with b_col:
            b_score=st.number_input(
                f"Rounds do {team_b or 'Time B'} · mapa {index}",
                min_value=0,max_value=80,step=1,
                value=int(m.get("team_b_score") or 0),
                key="edb_confront_score_b_"+mid
            )
        scores[mid]=(a_score,b_score)

    st.caption("Os placares precisam somar os rounds de cada mapa. "
               "O resultado da série é calculado a partir dos resultados individuais.")
    confirmed=st.checkbox(
        "Conferi os placares, os 10 jogadores e a divisão das equipes.",
        key="edb_confront_confirm"
    )
    if st.button(
        f"Registrar {chosen_format} na temporada",
        disabled=not confirmed,type="primary",key="edb_confront_submit"
    ):
        try:
            payload=prepare_confront_bundle(
                season,chosen_format,chosen,matches,stats,
                selected_a,scores,team_a,team_b
            )
            # Transação server-side: cria a série, vincula os mapas e confirma vitórias.
            result=store._api(
                "POST","rpc/register_edb_confronto",
                payload={"p_bundle":payload}
            )
            clear_cache()
            st.success(f"{chosen_format} registrada. Os rankings foram atualizados.")
            st.rerun()
        except Exception as exc:
            st.error("Não foi possível registrar o confronto: "+str(exc))
