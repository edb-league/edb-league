"""Comparações e medalhas da EDB LEAGUE.

Usa partidas oficiais e IDs estáveis, não compara apelidos nem limita jogos por XP.
"""
from __future__ import annotations


MEDALS = (
    {"id": "estreia", "name": "Estreia", "tier": "bronze",
     "description": "Participar da primeira partida", "metric": "games", "target": 1},
    {"id": "regular", "name": "Presença constante", "tier": "silver",
     "description": "Participar de 5 partidas", "metric": "games", "target": 5},
    {"id": "veterano", "name": "Veterano", "tier": "gold",
     "description": "Participar de 15 partidas", "metric": "games", "target": 15},
    {"id": "primeira_vitoria", "name": "Primeira vitória", "tier": "bronze",
     "description": "Vencer a primeira partida", "metric": "wins", "target": 1},
    {"id": "vencedor", "name": "Vencedor consistente", "tier": "silver",
     "description": "Vencer 5 partidas", "metric": "wins", "target": 5},
    {"id": "colecionador", "name": "Colecionador de vitórias", "tier": "gold",
     "description": "Vencer 15 partidas", "metric": "wins", "target": 15},
    {"id": "artilheiro", "name": "Artilheiro", "tier": "bronze",
     "description": "Somar 50 kills na liga", "metric": "kills", "target": 50},
    {"id": "exterminador", "name": "Exterminador", "tier": "silver",
     "description": "Somar 150 kills na liga", "metric": "kills", "target": 150},
    {"id": "lenda", "name": "Lenda das eliminações", "tier": "gold",
     "description": "Somar 300 kills na liga", "metric": "kills", "target": 300},
    {"id": "vinte_balas", "name": "20 eliminações", "tier": "bronze",
     "description": "Fazer 20 kills em uma partida", "metric": "peak_kills", "target": 20},
    {"id": "trinta_balas", "name": "30 eliminações", "tier": "gold",
     "description": "Fazer 30 kills em uma partida", "metric": "peak_kills", "target": 30},
    {"id": "parceiro", "name": "Companheiro de equipe", "tier": "silver",
     "description": "Fazer 10 assistências em uma partida", "metric": "peak_assists", "target": 10},
    {"id": "artilheiro_utility", "name": "Especialista em utilitárias", "tier": "silver",
     "description": "Causar 100 de dano de granadas em uma partida",
     "metric": "peak_grenade", "target": 100},
    {"id": "precisao", "name": "Impacto decisivo", "tier": "gold",
     "description": "Alcançar 120 ADR em uma partida de pelo menos 8 rounds",
     "metric": "peak_adr", "target": 120},
)


def achievements(player_id, records):
    """Todas as medalhas com progresso; métricas indisponíveis ficam indeterminadas."""
    rows = [r for r in records if r["player_id"] == str(player_id)]
    adr = [r["adr"] for r in rows if r["adr"] is not None and r["rounds"] >= 8]
    nades = [r["grenade_damage"] for r in rows if r["grenade_damage"] is not None]
    values = {
        "games": len(rows),
        "wins": sum(r["won"] is True for r in rows),
        "kills": sum(r["kills"] for r in rows),
        "peak_kills": max((r["kills"] for r in rows), default=0),
        "peak_assists": max((r["assists"] for r in rows), default=0),
        "peak_grenade": max(nades) if nades else None,
        "peak_adr": max(adr) if adr else None,
    }
    medals = []
    for rule in MEDALS:
        current = values[rule["metric"]]
        awarded = current is not None and current >= rule["target"]
        medals.append({
            **rule, "current": current, "earned": awarded,
            "progress": min(100, round(100 * current / rule["target"]))
                        if current is not None else None,
        })
    return medals


def compare_players(first_id, second_id, records):
    """Comparações de carreira e das partidas comuns.

    Confronto direto = ambos participaram de lados opostos, com resultados conhecidos.
    Não há dados de abates de um jogador especificamente sobre o outro.
    """
    a, b = str(first_id), str(second_id)
    if a == b:
        raise ValueError("Selecione dois jogadores diferentes")
    from league_legacy import player_summary
    totals = {pid: player_summary(pid, records) for pid in (a, b)}
    left = {r["match_id"]: r for r in totals[a]["matches"]}
    right = {r["match_id"]: r for r in totals[b]["matches"]}
    shared = []
    h2h = {a: 0, b: 0}
    opponent_games = 0
    teammate_games = 0
    for mid in sorted(left.keys() & right.keys(), key=lambda x:(left[x]["date"], x)):
        x, y = left[mid], right[mid]
        side = ("Mesmo time" if x["won"] is not None and x["won"] == y["won"]
                else "Adversários" if x["won"] is not None and y["won"] is not None
                else "Lados não confirmados")
        if side == "Adversários":
            opponent_games += 1
            if x["won"] is True and y["won"] is False:
                h2h[a] += 1
            elif y["won"] is True and x["won"] is False:
                h2h[b] += 1
        elif side == "Mesmo time":
            teammate_games += 1
        shared.append({
            "match_id": mid, "date": x["date"], "map": x["map"], "side": side,
            "first": x, "second": y,
        })
    return {
        "ids": (a, b), "first": totals[a], "second": totals[b],
        "shared": shared, "shared_count": len(shared), "head_to_head": h2h,
        "opponent_games": opponent_games, "teammate_games": teammate_games,
    }
