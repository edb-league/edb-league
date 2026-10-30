"""Votação de MVP da partida: quem jogou o mapa vota em outro jogador do mesmo mapa.

Regras: só vota quem entrou com a Steam e jogou o mapa; não pode votar em si mesmo; um voto por pessoa, que pode
ser trocado enquanto a votação está aberta (7 dias depois do mapa ou até todos votarem). Os resultados só aparecem
depois que a votação fecha, e ninguém vê quem votou em quem. O MVP da partida é só um reconhecimento: não entra nos
rankings, no XP nem nos títulos. Sem a tabela match_mvp_votes no banco (ou com o banco local), o recurso fica
indisponível e o resto do site segue normal.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from edb.steam_profile import normalize_steamid64

from . import settings
from .service import LeagueService, Snap
from .views import Conflict, NotFound, _parse_date, player_for_steamid

TABLE = "match_mvp_votes"
VOTE_DAYS = 7   # padrão; EDB_MVP_VOTE_DAYS muda a janela (usado nos testes de navegador)


def _vote_days() -> int:
    raw = settings.env("EDB_MVP_VOTE_DAYS").strip()
    return int(raw) if raw.isdigit() and 0 < int(raw) <= 36500 else VOTE_DAYS


def _participants(snap: Snap, match_id: str) -> list[str]:
    seen: list[str] = []
    for row in snap.stats:
        pid = str(row["player_id"])
        if str(row["match_id"]) == match_id and pid in snap.players_by_id and pid not in seen:
            seen.append(pid)
    return seen


def _match_day(snap: Snap, match_id: str) -> date | None:
    row = next((m for m in snap.matches if str(m["id"]) == match_id), None)
    return _parse_date(row.get("played_at")) if row else None


def _read_votes(service: LeagueService, match_id: str) -> list[dict] | None:
    """Votos da partida, ou None quando o banco não suporta (offline ou tabela ainda não criada)."""
    store = service.store
    if not store.cloud:
        return None
    try:
        return store._api("GET", TABLE, params={"select": "*", "match_id": f"eq.{match_id}"})
    except RuntimeError:
        return None


def _state(snap: Snap, match_id: str):
    """(participantes, último dia de votação) ou NotFound."""
    day = _match_day(snap, match_id)
    people = _participants(snap, match_id)
    if day is None:
        raise NotFound("Partida não encontrada.")
    return people, day + timedelta(days=_vote_days())


def build_mvp(service: LeagueService, match_id: str, steamid: str | None) -> dict:
    snap = service.snap()
    people, closes_on = _state(snap, match_id)
    votes = _read_votes(service, match_id)
    base = {"closes_on": closes_on.isoformat(), "electorate": len(people)}
    viewer = {"logged_in": steamid is not None, "player_id": None, "can_vote": False, "my_vote": None, "reason": None}
    if votes is None or len(people) < 2:
        return {**base, "status": "unavailable", "votes_cast": 0, "candidates": [], "viewer": viewer, "results": None}

    me = player_for_steamid(snap, steamid) if steamid else None
    my_id = str(me["id"]) if me else None
    mine = next((v for v in votes if str(v["voter_id"]) == my_id), None) if my_id else None
    cast = len({str(v["voter_id"]) for v in votes})
    closed = snap.today > closes_on or cast >= len(people)
    viewer["player_id"] = my_id
    viewer["my_vote"] = str(mine["candidate_id"]) if mine else None
    if steamid is None:
        viewer["reason"] = "Entre com a Steam para votar."
    elif my_id is None:
        viewer["reason"] = "Seu SteamID não está cadastrado na liga."
    elif my_id not in people:
        viewer["reason"] = "Só quem jogou este mapa pode votar."
    elif closed:
        viewer["reason"] = "A votação está encerrada."
    else:
        viewer["can_vote"] = True

    results = None
    if closed:
        tally: dict[str, int] = {}
        for v in votes:
            tally[str(v["candidate_id"])] = tally.get(str(v["candidate_id"]), 0) + 1
        top = max(tally.values(), default=0)
        results = [{"player": {"id": pid, "name": snap.name_of(pid)}, "votes": n, "mvp": n == top}
                   for pid, n in sorted(tally.items(), key=lambda kv: (-kv[1], snap.name_of(kv[0]).casefold()))]
    return {
        **base, "status": "closed" if closed else "open", "votes_cast": cast,
        "candidates": [{"id": pid, "name": snap.name_of(pid)} for pid in people if pid != my_id],
        "viewer": viewer, "results": results,
    }


def cast_vote(service: LeagueService, match_id: str, steamid: str | None, candidate_id: str) -> dict:
    snap = service.snap()
    people, closes_on = _state(snap, match_id)
    if _read_votes(service, match_id) is None or len(people) < 2:
        raise ValueError("A votação de MVP não está disponível para esta partida.")
    if steamid is None:
        raise PermissionError("Entre com a Steam para votar.")
    me = player_for_steamid(snap, normalize_steamid64(steamid) or steamid)
    if me is None or str(me["id"]) not in people:
        raise PermissionError("Só quem jogou este mapa pode votar.")
    voter = str(me["id"])
    if snap.today > closes_on:
        raise Conflict("A votação deste mapa já foi encerrada.")
    cast = {str(v["voter_id"]) for v in _read_votes(service, match_id) or []}
    if len(cast) >= len(people):
        raise Conflict("A votação deste mapa já foi encerrada.")
    if candidate_id == voter:
        raise ValueError("Você não pode votar em si mesmo.")
    if candidate_id not in people:
        raise ValueError("Escolha um jogador que participou deste mapa.")
    service.store._upsert(TABLE, {
        "match_id": match_id, "voter_id": voter, "candidate_id": candidate_id,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }, "match_id,voter_id")
    return build_mvp(service, match_id, steamid)
