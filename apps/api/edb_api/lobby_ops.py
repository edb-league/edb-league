"""Lobby de partida: dois times de 5, o primeiro de cada time é o capitão, JSON do MatchZy com 10/10."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from threading import RLock

from fastapi import HTTPException
from edb.steam_profile import normalize_steamid64

from .service import LeagueService, Snap, safe_level
from .views import Conflict, NotFound, player_for_steamid

_lock = RLock()

TEAM_SIZE = 5
SPECTATOR_SLOTS = 5
FORMATS = {"md1": 1, "md3": 3, "md5": 5}
MAPS = {
    "de_mirage": "Mirage", "de_inferno": "Inferno", "de_nuke": "Nuke", "de_ancient": "Ancient",
    "de_anubis": "Anubis", "de_dust2": "Dust II", "de_overpass": "Overpass",
}
DEFAULT_MAP = "de_mirage"
DEFAULT_FORMAT = "md1"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _new() -> dict:
    return {"map": DEFAULT_MAP, "format": DEFAULT_FORMAT, "team1": [], "team2": [], "spectators": [], "updated_at": _now()}


def _state(service: LeagueService) -> dict:
    state = service.store.lobby_get() or _new()
    state.setdefault("spectators", [])
    return state


def _save(service: LeagueService, state: dict) -> None:
    state["updated_at"] = _now()
    service.store.lobby_put(state)


def _member(snap: Snap, pid: str) -> dict:
    player = snap.players_by_id.get(str(pid))
    return {"id": str(pid), "name": snap.name_of(pid), "level": safe_level(player) if player else 5}


def _team_view(snap: Snap, team: list[str]) -> list[dict]:
    return [{**_member(snap, pid), "captain": index == 0} for index, pid in enumerate(team)]


def view(service: LeagueService, viewer_id: str | None = None, is_admin: bool = False) -> dict:
    """Estado público do lobby. Nunca devolve SteamID."""
    state = _state(service)
    snap = service.snap()
    team1, team2 = state["team1"], state["team2"]
    full = len(team1) == TEAM_SIZE and len(team2) == TEAM_SIZE
    spectators = state["spectators"]
    mine = 1 if viewer_id in team1 else 2 if viewer_id in team2 else 0 if viewer_id in spectators else None
    captain_ids = [t[0] for t in (team1, team2) if t]
    can_configure = is_admin or (viewer_id is not None and viewer_id in captain_ids)
    return {
        "team_size": TEAM_SIZE, "map": state["map"], "format": state["format"],
        "maps": [{"id": k, "name": v} for k, v in MAPS.items()],
        "formats": [{"id": k, "maps": v} for k, v in FORMATS.items()],
        "teams": [{"id": 1, "players": _team_view(snap, team1)}, {"id": 2, "players": _team_view(snap, team2)}],
        "spectators": {"slots": SPECTATOR_SLOTS, "players": _team_view(snap, spectators)},
        "count": len(team1) + len(team2), "ready": full,
        "me": {"player_id": viewer_id, "team": mine, "can_configure": can_configure, "is_admin": is_admin,
               "can_get_json": full and (is_admin or mine is not None)},
        "updated_at": state["updated_at"],
    }


def _check_player(service: LeagueService, steamid: str | None) -> dict:
    if not steamid:
        raise HTTPException(401, "Entre com a Steam para participar do lobby.")
    player = player_for_steamid(service.snap(), steamid)
    if player is None:
        raise HTTPException(403, "Seu SteamID não está no elenco da liga.")
    if str(player.get("is_active", 1)) in ("0", "False", "false"):
        raise HTTPException(403, "Jogador inativo no elenco.")
    return player


def join(service: LeagueService, steamid: str | None, team: int) -> str:
    """Entra no time. Quem entra primeiro vira capitão. Devolve o id do jogador."""
    if team not in (0, 1, 2):
        raise ValueError("Time inválido.")
    player = _check_player(service, steamid)
    pid = str(player["id"])
    with _lock:
        state = _state(service)
        if pid in state["team1"] or pid in state["team2"] or pid in state["spectators"]:
            raise Conflict("Você já está no lobby. Saia do time atual antes de trocar.")
        target = state["spectators"] if team == 0 else state[f"team{team}"]
        if len(target) >= (SPECTATOR_SLOTS if team == 0 else TEAM_SIZE):
            raise Conflict("Esse time já está completo." if team else "Os slots de espectador estão cheios.")
        target.append(pid)
        _save(service, state)
    return pid


def leave(service: LeagueService, steamid: str | None) -> str:
    player = _check_player(service, steamid)
    pid = str(player["id"])
    with _lock:
        state = _state(service)
        for key in ("team1", "team2", "spectators"):
            if pid in state[key]:
                state[key].remove(pid)  # o próximo da fila passa a ser o capitão
                _save(service, state)
                return pid
    raise NotFound("Você não está no lobby.")


def remove(service: LeagueService, player_id: str) -> None:
    """Admin: tira alguém do lobby."""
    with _lock:
        state = _state(service)
        for key in ("team1", "team2", "spectators"):
            if str(player_id) in state[key]:
                state[key].remove(str(player_id))
                _save(service, state)
                return
    raise NotFound("Esse jogador não está no lobby.")


def configure(service: LeagueService, steamid: str | None, is_admin: bool, map_id: str | None, fmt: str | None) -> None:
    if map_id is not None and map_id not in MAPS:
        raise ValueError("Mapa inválido.")
    if fmt is not None and fmt not in FORMATS:
        raise ValueError("Formato inválido.")
    with _lock:
        state = _state(service)
        if not is_admin:
            player = _check_player(service, steamid)
            captains = [t[0] for t in (state["team1"], state["team2"]) if t]
            if str(player["id"]) not in captains:
                raise HTTPException(403, "Só os capitães (ou o admin) configuram o lobby.")
        if map_id is not None:
            state["map"] = map_id
        if fmt is not None:
            state["format"] = fmt
        _save(service, state)


def reset(service: LeagueService) -> None:
    with _lock:
        service.store.lobby_delete()


def matchzy_config(service: LeagueService, steamid: str | None, is_admin: bool) -> dict:
    """JSON de partida do MatchZy (10/10). Só quem está no lobby ou o admin."""
    with _lock:
        state = _state(service)
    pid = None
    if not is_admin:
        pid = str(_check_player(service, steamid)["id"])
        if pid not in state["team1"] and pid not in state["team2"] and pid not in state["spectators"]:
            raise HTTPException(403, "Só quem está no lobby recebe o JSON da partida.")
    if len(state["team1"]) != TEAM_SIZE or len(state["team2"]) != TEAM_SIZE:
        raise Conflict("O lobby precisa estar completo (5 contra 5).")
    snap = service.snap()

    def team_block(ids: list[str]) -> dict:
        players = {}
        for member in ids:
            raw = snap.players_by_id[str(member)].get("steamid")
            sid = normalize_steamid64(raw)
            if not sid:
                raise ValueError(f"{snap.name_of(member)} não tem SteamID válido no cadastro.")
            players[sid] = snap.name_of(member)
        return {"name": f"team_{snap.name_of(ids[0])}", "players": players}

    def _spectators(snap_: Snap, ids: list[str]) -> dict:
        out = {}
        for member in ids:
            sid = normalize_steamid64(snap_.players_by_id[str(member)].get("steamid"))
            if sid:
                out[sid] = snap_.name_of(member)
        return out

    count = FORMATS[state["format"]]
    pool = [state["map"]] if count == 1 else list(MAPS)
    if count > 1:
        pool.remove(state["map"])
        pool.insert(0, state["map"])
    return {
        "matchid": int(datetime.now(timezone.utc).timestamp()),
        "num_maps": count,
        "players_per_team": TEAM_SIZE,
        "min_players_to_ready": 1,
        "skip_veto": count == 1,
        "veto_first": "team1",
        "side_type": "standard",
        "maplist": pool,
        "team1": team_block(state["team1"]),
        "team2": team_block(state["team2"]),
        "spectators": {"players": _spectators(snap, state["spectators"])},
        "cvars": {"hostname": "EDB League"},
    }


def matchzy_json(config: dict) -> str:
    return json.dumps(config, ensure_ascii=False, indent=2)
