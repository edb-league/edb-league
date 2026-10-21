"""Rotas administrativas protegidas por cookie assinado."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile
from pydantic import BaseModel, Field, field_validator

from . import admin_ops, auth, settings
from .service import get_service

router = APIRouter(prefix="/api/admin")
protected = [Depends(auth.require_admin)]


class LoginBody(BaseModel):
    password: str


class PlayerCreate(BaseModel):
    nickname: str = Field(min_length=1, max_length=60)
    steamid: str | None = None
    skill_level: int = Field(default=5, ge=1, le=10)


class PlayerPatch(BaseModel):
    nickname: str | None = Field(default=None, min_length=1, max_length=60)
    steamid: str | None = None
    skill_level: int | None = Field(default=None, ge=1, le=10)


class ConfrontBody(BaseModel):
    season: int
    format: str
    match_ids: list[str]
    team_a_ids: list[str]
    scores: dict[str, list[int]]
    team_a_name: str = "PT"
    team_b_name: str = "PL"

    @field_validator("scores")
    @classmethod
    def _pairs(cls, value):
        if any(len(pair) != 2 for pair in value.values()):
            raise ValueError("Cada placar precisa de dois valores.")
        return value


class ImportPlayerBody(BaseModel):
    nickname: str
    steamid: str = ""
    kills: int = Field(default=0, ge=0)
    deaths: int = Field(default=0, ge=0)
    assists: int = Field(default=0, ge=0)
    damage: int | None = None
    rounds: int = Field(default=0, ge=0)
    headshots: int = Field(default=0, ge=0)
    plants: int = Field(default=0, ge=0)
    defuses: int = Field(default=0, ge=0)
    rating: float | None = None
    kast: float | None = None
    open_kills: int | None = None
    trade_kills: int | None = None
    won: bool | None = None


class ImportCommitBody(BaseModel):
    fingerprint: str
    source: str
    played_at: str
    map_name: str = ""
    rounds_total: int
    note: str = ""
    players: list[ImportPlayerBody]
    winners: list[str] = []


# Sessão ----------------------------------------------------------------------------
@router.get("/session")
def session(request: Request):
    return {"authenticated": auth.verify_token(request.cookies.get(auth.COOKIE_NAME)),
            "configured": settings.admin_configured()}


@router.post("/login")
def login(body: LoginBody, request: Request, response: Response):
    auth.check_origin(request)
    if not settings.admin_configured():
        raise HTTPException(503, "Administração bloqueada: configure XINXAS_ADMIN_PASSWORD no servidor.")
    ip = auth.client_ip(request)
    auth.ensure_not_locked(ip)
    if not auth.check_password(body.password):
        auth.register_failure(ip)
        raise HTTPException(401, "Senha incorreta.")
    auth.clear_failures(ip)
    auth.set_cookie(response)
    return {"ok": True}


@router.post("/logout")
def logout(request: Request, response: Response):
    auth.check_origin(request)
    auth.clear_cookie(response)
    return {"ok": True}


# Elenco ----------------------------------------------------------------------------
@router.get("/overview", dependencies=protected)
def overview():
    return admin_ops.overview(get_service())


@router.post("/players", dependencies=protected)
def create_player(body: PlayerCreate):
    return admin_ops.create_player(get_service(), body.nickname, body.steamid, body.skill_level)


@router.patch("/players/{player_id}", dependencies=protected)
def update_player(player_id: str, body: PlayerPatch):
    return admin_ops.update_player(get_service(), player_id, body.model_dump(exclude_unset=True))


@router.post("/players/{player_id}/archive", dependencies=protected)
def archive_player(player_id: str):
    return admin_ops.set_active(get_service(), player_id, False)


@router.post("/players/{player_id}/reactivate", dependencies=protected)
def reactivate_player(player_id: str):
    return admin_ops.set_active(get_service(), player_id, True)


# Temporadas e confrontos -----------------------------------------------------------
@router.post("/seasons/{number}/homologate", dependencies=protected)
def homologate(number: int):
    return admin_ops.homologate(get_service(), number)


@router.get("/confront/candidates", dependencies=protected)
def confront_candidates(season: int):
    return admin_ops.confront_candidates(get_service(), season)


@router.post("/confront", dependencies=protected)
def confront(body: ConfrontBody):
    return admin_ops.register_confront(get_service(), body.model_dump())


# Importação e backup ---------------------------------------------------------------
@router.post("/import/preview", dependencies=protected)
def import_preview(method: str = Form(...), file: UploadFile | None = File(default=None)):
    return admin_ops.preview_import(get_service(), method, file)


@router.post("/import/commit", dependencies=protected)
def import_commit(body: ImportCommitBody):
    return admin_ops.commit_import(get_service(), body.model_dump())


@router.get("/export/{kind}.csv", dependencies=protected)
def export(kind: str):
    content, filename = admin_ops.export_csv(get_service(), kind)
    return Response(content, media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})
