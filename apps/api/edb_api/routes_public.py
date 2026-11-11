"""Rotas públicas, somente leitura."""
from __future__ import annotations

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, Field

from . import auth, draft_ops, views
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
