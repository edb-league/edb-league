"""Draft de campeonato: leitura pública e ações do administrador."""
from __future__ import annotations

from datetime import datetime, timezone
from threading import RLock

from edb import draft as engine

from .service import LeagueService, Snap, safe_level
from .views import NotFound

_lock = RLock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _player(snap: Snap, pid: str) -> dict:
    player = snap.players_by_id.get(str(pid))
    return {"id": str(pid), "name": snap.name_of(pid), "level": safe_level(player) if player else 5}


def view(service: LeagueService) -> dict:
    """Estado público do draft. Sem draft criado: {"exists": false}."""
    state = service.store.draft_get()
    if not state:
        return {"exists": False}
    snap = service.snap()
    turn = engine.next_pick(state)
    teams = []
    for team in state["teams"]:
        captain = _player(snap, team["captain_id"])
        picks = [{"number": next(p["n"] for p in state["picks"] if p["player_id"] == pid), "player": _player(snap, pid)}
                 for pid in team["picks"]]
        members = [captain, *[p["player"] for p in picks]]
        teams.append({"id": team["id"], "name": team["name"], "captain": captain, "picks": picks,
                      "level_sum": sum(m["level"] for m in members)})
    available = sorted((_player(snap, pid) for pid in engine.available(state)),
                       key=lambda p: (-p["level"], p["name"].casefold()))
    current = None
    if turn:
        current = {"number": turn["number"], "total": turn["total"], "team_id": turn["team"],
                   "team_name": state["teams"][turn["team"] - 1]["name"]}
    return {"exists": True, "name": state["name"], "status": state["status"], "team_size": state["team_size"],
            "teams": teams, "available": available, "next": current, "picks_made": len(state["picks"]),
            "updated_at": state["updated_at"]}


def create(service: LeagueService, body: dict) -> dict:
    with _lock:
        if service.store.draft_get():
            raise ValueError("Já existe um draft. Reinicie o atual antes de criar outro.")
        snap = service.snap()
        known = {str(p["id"]) for p in snap.active_players}
        ids = [str(t.get("captain_id")) for t in body["teams"]] + [str(p) for p in body["pool_ids"]]
        if any(pid not in known for pid in ids):
            raise ValueError("Só jogadores ativos do elenco podem participar do draft.")
        state = engine.create_draft(body["name"], int(body["team_size"]), body["teams"], body["pool_ids"], _now(),
                                    snake=bool(body.get("snake", True)))
        service.store.draft_put(state)
    return view(service)


def _load(service: LeagueService) -> dict:
    state = service.store.draft_get()
    if not state:
        raise NotFound("Nenhum draft em andamento.")
    return state


def pick(service: LeagueService, player_id: str) -> dict:
    with _lock:
        state = engine.apply_pick(_load(service), player_id, _now())
        service.store.draft_put(state)
    return view(service)


def undo(service: LeagueService) -> dict:
    with _lock:
        state = engine.undo_pick(_load(service), _now())
        service.store.draft_put(state)
    return view(service)


def reset(service: LeagueService) -> dict:
    with _lock:
        service.store.draft_delete()
    return {"exists": False}
