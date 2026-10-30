"""Login com a Steam e dados de quem está logado.

Fluxo: /api/auth/steam/login envia o visitante à Steam; a Steam o devolve a /api/auth/steam/callback;
o servidor confirma com a Steam, confere se o SteamID é de um jogador cadastrado (ou do admin) e só então
cria a sessão. Quem não está cadastrado não ganha sessão nenhuma.
"""
from __future__ import annotations

import hmac
import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from . import auth, identity, privacy, settings, steam_openid, views
from .service import get_service
from .serializers import CleanJSONResponse

log = logging.getLogger("edb.auth")

router = APIRouter()


def _return_to(state: str) -> str:
    return f"{settings.public_url()}/api/auth/steam/callback?state={state}"


def _redirect(path: str) -> RedirectResponse:
    return RedirectResponse(path, status_code=303)


def _lock_key(request: Request) -> str:
    return "steam|" + auth.client_ip(request)


@router.get("/api/auth/steam/login")
def steam_login(request: Request, next: str = "/"):
    if not settings.steam_login_enabled():
        raise HTTPException(503, "Login com a Steam não está configurado neste servidor.")
    auth.ensure_not_locked(_lock_key(request))
    response = _redirect("/")
    state = identity.new_state(response, next)
    response.headers["location"] = steam_openid.login_url(_return_to(state), settings.public_url())
    return response


@router.get("/api/auth/steam/callback")
def steam_callback(request: Request):
    if not settings.steam_login_enabled():
        raise HTTPException(503, "Login com a Steam não está configurado neste servidor.")
    key = _lock_key(request)
    auth.ensure_not_locked(key)

    def fail(reason: str) -> RedirectResponse:
        auth.register_failure(key)
        out = _redirect(f"/?login={reason}")
        identity.clear_state(out)
        return out

    pending = identity.read_state(request)
    state = request.query_params.get("state", "")
    # O valor aleatório do cookie precisa ser o mesmo que voltou na URL: impede forçar o login de outra pessoa.
    if pending is None or not hmac.compare_digest(pending[0].encode("utf-8"), state.encode("utf-8")):
        return fail("erro")
    steamid = steam_openid.verify(dict(request.query_params), _return_to(state))
    if steamid is None:
        return fail("erro")

    player = views.player_for_steamid(get_service().snap(), steamid)
    is_admin = settings.admin_steamid() == steamid
    if player is None and not is_admin:
        out = _redirect("/?login=desconhecido")
        identity.clear_state(out)
        return out
    out = _redirect(pending[1])
    identity.set_session(out, steamid)
    identity.clear_state(out)
    auth.clear_failures(key)
    log.info("Login pela Steam: %s", "admin" if is_admin else "jogador")
    return out


@router.get("/api/me")
def me(request: Request):
    steamid = identity.session_steamid(request)
    service = get_service()
    payload = views.build_me(service, steamid, auth.steam_admin(request))
    return CleanJSONResponse(payload)


class PrivacyBody(BaseModel):
    hide_avatar: bool
    hide_persona: bool
    hide_hours: bool


def _my_player_id(request: Request) -> str | None:
    steamid = identity.session_steamid(request)
    player = views.player_for_steamid(get_service().snap(), steamid) if steamid else None
    return str(player["id"]) if player else None


@router.get("/api/me/privacy")
def my_privacy(request: Request):
    return CleanJSONResponse(privacy.build_mine(get_service(), _my_player_id(request)))


@router.post("/api/me/privacy")
def save_my_privacy(body: PrivacyBody, request: Request):
    auth.check_origin(request)
    player_id = _my_player_id(request)
    if player_id is None:
        raise HTTPException(401, "Entre com a Steam, na conta de um jogador cadastrado, para mudar a privacidade.")
    return CleanJSONResponse(privacy.save_mine(get_service(), player_id, body.model_dump()))


@router.post("/api/auth/logout")
def logout(request: Request):
    auth.check_origin(request)
    response = CleanJSONResponse({"ok": True})
    identity.clear_session(response)
    return response
