"""Ranking BAGRES e Prêmio Henio por menor ADR ponderado por rounds.

Usa os mapas completos do período, nunca o recorte de seis melhores mapas dos
títulos oficiais. Não altera Elite, Superação, XP nem resultados homologados.
"""
from __future__ import annotations

from collections import defaultdict
from math import isfinite

import pandas as pd


def _number(value):
    try:
        number=float(value)
        return number if isfinite(number) else None
    except (TypeError,ValueError):
        return None


def _players_with_adr(records, name_key):
    """Agrupa por identidade; exige dano e rounds em todos os mapas do atleta."""
    groups=defaultdict(dict)
    for record in records:
        pid=str(record.get("player_id") or "")
        mid=str(record.get("match_id") or "")
        if not pid or not mid:
            continue
        groups[pid][mid]=record

    board=[]
    for pid, unique in groups.items():
        played=list(unique.values())
        if not played:
            continue
        measured=[(r,_number(r.get("damage")),_number(r.get("rounds")))
                  for r in played]
        if any(dmg is None or rounds is None or rounds<=0
               for _,dmg,rounds in measured):
            continue
        rounds_total=sum(rounds for _,_,rounds in measured)
        damage_total=sum(dmg for _,dmg,_ in measured)
        kills=sum(int(_number(r.get("kills")) or 0) for r in played)
        deaths=sum(int(_number(r.get("deaths")) or 0) for r in played)
        name=str(played[0].get(name_key) or pid)
        board.append({
            "player_id":pid,"name":name,"maps":len(played),
            "rounds":rounds_total,"damage":damage_total,
            "adr":damage_total/rounds_total,
            "kills":kills,"deaths":deaths,
            "wins":sum(r.get("won") is True for r in played),
        })
    return sorted(board,key=lambda x:(x["adr"],x["name"].casefold(),x["player_id"]))


def bagres_board(frame: pd.DataFrame, levels=None):
    """Ordena pior ADR em primeiro usando TODOS os mapas da temporada."""
    cols=["player_id","Jogador","Nível","Estrelas","Partidas","Kills",
          "K/D","KPR","ADR","Vitórias","Elegível"]
    if frame.empty:
        return pd.DataFrame(columns=cols)
    levels=levels or {}
    source=frame.to_dict("records")
    ranked=_players_with_adr(source,"nickname")
    rows=[]
    for player in ranked:
        pid=player["player_id"]
        rows.append({
            "player_id":pid,"Jogador":player["name"],
            "Nível":levels.get(pid),"Estrelas":0,
            "Partidas":player["maps"],"Kills":player["kills"],
            "K/D":round(player["kills"]/player["deaths"],2)
                    if player["deaths"] else None,
            "KPR":round(player["kills"]/player["rounds"],3),
            "ADR":round(player["adr"],1),"Vitórias":player["wins"],
            "Elegível":player["maps"]>=2,
            "__adr_precise":player["adr"],
        })
    return pd.DataFrame(rows,columns=cols+["__adr_precise"])


def premio_henio(records, min_maps=2):
    """Pior ADR de carreira, exigindo ao menos 2 mapas com medição completa.

    O nome do prêmio é fixo, mas o homenageado muda conforme as estatísticas.
    Empates exatos são compartilhados.
    """
    board=[x for x in _players_with_adr(records,"player_name")
           if x["maps"]>=min_maps]
    if not board:
        return None
    minimum=board[0]["adr"]
    leaders=[p for p in board if abs(p["adr"]-minimum)<1e-9]
    return {
        "adr":minimum,
        "holders":[{"id":p["player_id"],"name":p["name"],"maps":p["maps"]}
                   for p in leaders],
        "min_maps":min_maps,
    }
