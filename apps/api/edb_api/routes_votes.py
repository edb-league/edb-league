"""Votação de MVP da partida. As respostas dependem de quem está logado, por isso nunca ficam em cache."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from . import auth, identity, mvp
from .service import get_service

router = APIRouter(prefix="/api/votes")


class VoteBody(BaseModel):
    player_id: str


@router.get("/mvp/{match_id}")
def read(match_id: str, request: Request):
    return mvp.build_mvp(get_service(), match_id, identity.session_steamid(request))


@router.post("/mvp/{match_id}")
def vote(match_id: str, body: VoteBody, request: Request):
    auth.check_origin(request)
    try:
        return mvp.cast_vote(get_service(), match_id, identity.session_steamid(request), body.player_id)
    except PermissionError as exc:
        raise HTTPException(401 if identity.session_steamid(request) is None else 403, str(exc)) from exc
