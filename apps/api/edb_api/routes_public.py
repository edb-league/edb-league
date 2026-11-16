"""Rotas públicas, somente leitura."""
from __future__ import annotations

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, Field

from . import auth, draft_ops, identity, lobby_ops, views
from .service import get_service

router = APIRouter(prefix="/api")


class DrawBody(BaseModel):
    player_ids: list[str]


class DraftTeam(BaseModel):
    name: str = Field(max_length=30)
    captain_id: str


class DraftCreate(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    team_size: int = Field(default=5, ge=2, le=10)
    snake: bool = True
    teams: list[DraftTeam] = Field(min_length=2, max_length=8)
    pool_ids: list[str]


class LobbyJoin(BaseModel):
    team: int


class LobbyConfig(BaseModel):
    map: str | None = None
    format: str | None = None


class DraftPick(BaseModel):
    player_id: str


@router.get("/health")
def health():
    return {"ok": True}


@router.get("/meta")
def meta():
    return views.build_meta(get_service())


@router.get("/home")
def home(season: str | None = None):
    return views.build_home(get_service().snap(), season)


@router.get("/rankings/{rtype}")
def ranking(rtype: str, season: str | None = None):
    return views.build_ranking(get_service().snap(), season, rtype)


@router.get("/missions")
def missions(season: str | None = None):
    return views.build_missions(get_service().snap(), season)


@router.get("/steam/avatars")
def steam_avatars():
    return views.build_avatars(get_service())


@router.get("/players")
def players(include_inactive: bool = False):
    return views.build_players(get_service().snap(), include_inactive)


@router.get("/players/{player_id}")
def player_detail(player_id: str, lado: str | None = None, mapa: str | None = None,
                  formato: str | None = None, periodo: str | None = None):
    """Perfil do jogador. Os filtros (lado, mapa, formato, periodo) valem só para o bloco `advanced`."""
    service = get_service()
    filters = views._stat_filters(lado, mapa, formato, periodo)
    return views.build_player_detail(service, service.snap(), player_id, filters)


@router.get("/compare")
def compare(a: str, b: str):
    if a == b:
        raise ValueError("Escolha dois jogadores diferentes para comparar os resultados.")
    return views.build_compare(get_service().snap(), a, b)


@router.get("/hall-of-fame")
def hall_of_fame():
    return views.build_hall(get_service().snap())


@router.get("/medals")
def medals():
    return views.build_medals(get_service().snap())


@router.get("/matches")
def matches(season: str | None = None):
    return views.build_matches(get_service().snap(), season)


@router.get("/matches/{match_id}")
def match_detail(match_id: str):
    return views.build_match_detail(get_service().snap(), match_id)


@router.post("/draw")
def draw(body: DrawBody):
    return views.build_draw(get_service().snap(), body.player_ids)


@router.get("/draft")
def draft(response: Response):
    """Andamento do draft de campeonato. Sem cache: a página consulta de poucos em poucos segundos."""
    response.headers["Cache-Control"] = "no-store"
    return draft_ops.view(get_service())


@router.post("/draft")
def draft_create(body: DraftCreate, request: Request):
    auth.check_origin(request)
    return draft_ops.create(get_service(), body.model_dump())


@router.post("/draft/pick")
def draft_pick(body: DraftPick, request: Request):
    auth.check_origin(request)
    return draft_ops.pick(get_service(), body.player_id)


@router.post("/draft/undo")
def draft_undo(request: Request):
    auth.check_origin(request)
    return draft_ops.undo(get_service())


@router.delete("/draft")
def draft_reset(request: Request):
    auth.check_origin(request)
    return draft_ops.reset(get_service())


def _viewer(request: Request) -> tuple[str | None, bool]:
    return identity.session_steamid(request), auth.is_admin(request)


def _lobby_view(request: Request, pid: str | None = None):
    steamid, admin = _viewer(request)
    service = get_service()
    if pid is None and steamid:
        player = views.player_for_steamid(service.snap(), steamid)
        pid = str(player["id"]) if player else None
    return lobby_ops.view(service, pid, admin)


@router.get("/lobby")
def lobby(request: Request, response: Response):
    """Lobby da partida. Sem cache: a página consulta de poucos em poucos segundos."""
    response.headers["Cache-Control"] = "no-store"
    return _lobby_view(request)


@router.post("/lobby/join")
def lobby_join(body: LobbyJoin, request: Request):
    auth.check_origin(request)
    pid = lobby_ops.join(get_service(), identity.session_steamid(request), body.team)
    return _lobby_view(request, pid)


@router.post("/lobby/leave")
def lobby_leave(request: Request):
    auth.check_origin(request)
    lobby_ops.leave(get_service(), identity.session_steamid(request))
    return _lobby_view(request)


@router.patch("/lobby")
def lobby_config(body: LobbyConfig, request: Request):
    auth.check_origin(request)
    steamid, admin = _viewer(request)
    lobby_ops.configure(get_service(), steamid, admin, body.map, body.format)
    return _lobby_view(request)


@router.delete("/lobby/players/{player_id}")
def lobby_remove(player_id: str, request: Request):
    auth.require_admin(request)
    lobby_ops.remove(get_service(), player_id)
    return _lobby_view(request)


@router.delete("/lobby")
def lobby_reset(request: Request):
    auth.require_admin(request)
    lobby_ops.reset(get_service())
    return _lobby_view(request)


@router.get("/lobby/matchzy")
def lobby_matchzy(request: Request, response: Response):
    """JSON de partida do MatchZy; só para quem está no lobby (ou admin). Contém SteamIDs, por isso não é público."""
    response.headers["Cache-Control"] = "no-store"
    steamid, admin = _viewer(request)
    config = lobby_ops.matchzy_config(get_service(), steamid, admin)
    return {"config": config, "json": lobby_ops.matchzy_json(config)}
