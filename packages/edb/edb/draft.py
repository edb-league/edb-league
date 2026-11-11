"""Draft de campeonato: capitães escolhem jogadores em turnos (ordem em cobra).

O estado é um dicionário simples (guardado como JSON), sem nada ligado ao banco, para ser fácil de testar.
O capitão já conta como membro do próprio time; as escolhas completam o restante das vagas.
"""
from __future__ import annotations

MIN_TEAMS, MAX_TEAMS = 2, 8
MIN_TEAM_SIZE, MAX_TEAM_SIZE = 2, 10


def pick_sequence(team_count: int, team_size: int, snake: bool = True) -> list[int]:
    """Ordem dos times (números de 1 a team_count) em cada escolha: 1,2,3,4, 4,3,2,1, 1,2,3,4..."""
    order: list[int] = []
    for round_index in range(team_size - 1):
        teams = list(range(1, team_count + 1))
        if snake and round_index % 2 == 1:
            teams.reverse()
        order.extend(teams)
    return order


def create_draft(name: str, team_size: int, teams: list[dict], pool_ids: list[str], now: str, snake: bool = True) -> dict:
    """Monta um draft novo. `teams` traz `name` e `captain_id`; `pool_ids` são os jogadores a escolher (sem os capitães)."""
    name = str(name or "").strip()
    if not name:
        raise ValueError("Dê um nome ao draft.")
    if len(name) > 60:
        raise ValueError("O nome do draft pode ter no máximo 60 caracteres.")
    if not MIN_TEAM_SIZE <= team_size <= MAX_TEAM_SIZE:
        raise ValueError(f"Cada time precisa ter entre {MIN_TEAM_SIZE} e {MAX_TEAM_SIZE} jogadores.")
    if not MIN_TEAMS <= len(teams) <= MAX_TEAMS:
        raise ValueError(f"O draft precisa de {MIN_TEAMS} a {MAX_TEAMS} times.")

    built = []
    captains: list[str] = []
    names: set[str] = set()
    for index, team in enumerate(teams, 1):
        team_name = str(team.get("name") or "").strip()
        captain = str(team.get("captain_id") or "").strip()
        if not team_name or len(team_name) > 30:
            raise ValueError(f"O time {index} precisa de um nome de até 30 caracteres.")
        if team_name.casefold() in names:
            raise ValueError("Dois times não podem ter o mesmo nome.")
        if not captain:
            raise ValueError(f"Escolha o capitão do time {team_name}.")
        names.add(team_name.casefold())
        captains.append(captain)
        built.append({"id": index, "name": team_name, "captain_id": captain, "picks": []})
    if len(set(captains)) != len(captains):
        raise ValueError("Um jogador não pode ser capitão de dois times.")

    pool = [str(p) for p in pool_ids]
    if len(set(pool)) != len(pool):
        raise ValueError("A lista de jogadores tem nomes repetidos.")
    if set(pool) & set(captains):
        raise ValueError("Os capitães não entram na lista de jogadores a escolher.")
    needed = len(teams) * (team_size - 1)
    if len(pool) != needed:
        raise ValueError(
            f"Para {len(teams)} times de {team_size}, selecione {needed} jogadores além dos capitães (selecionados: {len(pool)})."
        )
    return {
        "name": name, "team_size": team_size, "snake": bool(snake), "status": "drafting",
        "teams": built, "pool": pool, "picks": [], "created_at": now, "updated_at": now,
    }


def available(state: dict) -> list[str]:
    taken = {pick["player_id"] for pick in state["picks"]}
    return [pid for pid in state["pool"] if pid not in taken]


def next_pick(state: dict) -> dict | None:
    """Próxima escolha: número (a partir de 1), total e time da vez; None quando o draft terminou."""
    sequence = pick_sequence(len(state["teams"]), state["team_size"], state.get("snake", True))
    done = len(state["picks"])
    if done >= len(sequence):
        return None
    return {"number": done + 1, "total": len(sequence), "team": sequence[done]}


def apply_pick(state: dict, player_id: str, now: str) -> dict:
    """Registra a escolha do time da vez e devolve o novo estado."""
    turn = next_pick(state)
    if turn is None:
        raise ValueError("O draft já terminou.")
    pid = str(player_id)
    if pid not in available(state):
        raise ValueError("Esse jogador não está disponível para escolha.")
    teams = [{**t, "picks": list(t["picks"])} for t in state["teams"]]
    teams[turn["team"] - 1]["picks"].append(pid)
    picks = [*state["picks"], {"n": turn["number"], "team": turn["team"], "player_id": pid}]
    status = "done" if turn["number"] >= turn["total"] else "drafting"
    return {**state, "teams": teams, "picks": picks, "status": status, "updated_at": now}


def undo_pick(state: dict, now: str) -> dict:
    """Desfaz a última escolha (o time e o número da vez voltam ao que eram)."""
    if not state["picks"]:
        raise ValueError("Ainda não há escolhas para desfazer.")
    last = state["picks"][-1]
    teams = [{**t, "picks": [p for p in t["picks"] if not (t["id"] == last["team"] and p == last["player_id"])]}
             for t in state["teams"]]
    return {**state, "teams": teams, "picks": state["picks"][:-1], "status": "drafting", "updated_at": now}
