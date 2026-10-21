"""Validacao local para registro seguro de confrontos BO1 / BO3 na EDB LEAGUE."""
from __future__ import annotations
from datetime import date


def prepare_confront_bundle(season, match_format, match_ids, matches, stats,
                           team_a_ids, scores, team_a_name="PT", team_b_name="PL"):
    """Valida dez atletas e placares; a gravação atômica ocorre no RPC do Supabase."""
    fmt=str(match_format).strip().lower()
    expected={"bo1":1,"bo3":3}.get(fmt)
    if expected is None:
        raise ValueError("Escolha BO1 ou BO3.")
    if len(match_ids)!=expected or len(set(match_ids))!=expected:
        raise ValueError(f"{fmt.upper()} precisa de exatamente {expected} mapa(s) distintos.")
    team_a=[str(pid) for pid in team_a_ids]
    if len(team_a)!=5 or len(set(team_a))!=5:
        raise ValueError("Selecione exatamente 5 atletas distintos do primeiro time.")
    if not str(team_a_name).strip() or not str(team_b_name).strip():
        raise ValueError("Os dois times precisam ter nome.")
    if str(team_a_name).strip().casefold()==str(team_b_name).strip().casefold():
        raise ValueError("Os times precisam ter nomes diferentes.")
    starts=date.fromisoformat(str(season["starts_on"])[:10])
    ends=date.fromisoformat(str(season["ends_on"])[:10])
    if season.get("homologated_at"):
        raise ValueError("A temporada já foi homologada.")
    if int(season["number"])<1:
        raise ValueError("A partir da Temporada 1, somente.")

    games={str(m["id"]):m for m in matches}
    by_match={}
    for stat in stats:
        mid=str(stat["match_id"])
        by_match.setdefault(mid,[]).append(str(stat["player_id"]))
    roster=None
    details=[]
    for mid in match_ids:
        mid=str(mid)
        match=games.get(mid)
        if match is None:
            raise ValueError(f"Mapa não encontrado: {mid}")
        played=date.fromisoformat(str(match["played_at"])[:10])
        if not starts<=played<=ends:
            raise ValueError(f"{match.get('map_name') or mid}: fora da temporada.")
        players=by_match.get(mid,[])
        if len(players)!=10 or len(set(players))!=10:
            raise ValueError(f"{match.get('map_name') or mid}: são necessários dez atletas diferentes.")
        if len(set(team_a)&set(players))!=5:
            raise ValueError("Os atletas do time PT/A precisam estar em todos os mapas.")
        if roster is None:
            roster=set(players)
        elif set(players)!=roster:
            raise ValueError("Os três mapas da BO3 precisam ter os mesmos dez atletas.")
        a,b=scores[mid]
        a,b=int(a),int(b)
        if a<0 or b<0 or a==b:
            raise ValueError("Informe um placar válido, sem empate.")
        rounds=match.get("rounds_total")
        if rounds is not None and a+b!=int(rounds):
            raise ValueError(f"Placar de {match.get('map_name') or mid}: soma {a+b}, mas o mapa tem {rounds} rounds.")
        details.append({"match_id":mid,"team_a_score":a,"team_b_score":b})
    return {
        "season_number":int(season["number"]),
        "format":fmt,"team_a_name":str(team_a_name).strip(),
        "team_b_name":str(team_b_name).strip(),
        "team_a_player_ids":team_a,
        "matches":details,
    }
