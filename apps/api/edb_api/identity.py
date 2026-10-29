"""Sessão de quem entrou com a Steam: cookie assinado (HMAC), sem estado no servidor.

O cookie só guarda o SteamID e a validade. Quem a pessoa é (jogador, admin) é recalculado a cada
requisição a partir dos dados atuais, então retirar alguém do elenco ou trocar o admin vale na hora.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import re
import secrets
import time

from fastapi import Request, Response

from . import settings

SESSION_COOKIE = "edb_session"
STATE_COOKIE = "edb_login"
SESSION_SECONDS = 14 * 24 * 60 * 60
STATE_SECONDS = 10 * 60
_STEAMID = re.compile(r"^7656119\d{10}$")
_SAFE_NEXT = re.compile(r"^/[A-Za-z0-9\-._~/%?=&#]*$")


def _sign(purpose: str, body: str) -> str:
    return hmac.new(settings.session_secret(), f"{purpose}|{body}".encode("utf-8"), hashlib.sha256).hexdigest()


def _pack(purpose: str, body: str, seconds: int) -> str:
    expiry = str(int(time.time()) + seconds)
    return f"{body}.{expiry}.{_sign(purpose, f'{body}.{expiry}')}"


def _unpack(purpose: str, token: str | None) -> str | None:
    if not token or token.count(".") < 2:
        return None
    rest, _, signature = token.rpartition(".")
    body, _, expiry = rest.rpartition(".")
    if not expiry.isdigit() or not hmac.compare_digest(signature, _sign(purpose, rest)):
        return None
    return body if int(expiry) > time.time() else None


def safe_next(path: str | None) -> str:
    """Só caminhos do próprio site: evita mandar a pessoa para outro endereço depois do login."""
    if not path or len(path) > 200 or path.startswith("//") or not _SAFE_NEXT.match(path):
        return "/"
    return path


def set_session(response: Response, steamid: str) -> None:
    response.set_cookie(
        SESSION_COOKIE, _pack("session", steamid, SESSION_SECONDS), max_age=SESSION_SECONDS,
        httponly=True, samesite="lax", secure=settings.cookie_secure(), path="/",
    )


def clear_session(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/", httponly=True, samesite="lax", secure=settings.cookie_secure())


def session_steamid(request: Request) -> str | None:
    """SteamID de quem tem sessão válida, ou None."""
    if not settings.steam_login_enabled():
        return None
    value = _unpack("session", request.cookies.get(SESSION_COOKIE))
    return value if value and _STEAMID.match(value) else None


def new_state(response: Response, next_path: str) -> str:
    """Cria o valor aleatório do login e o guarda num cookie curto, junto com o destino pós-login."""
    state = secrets.token_hex(16)
    destination = base64.urlsafe_b64encode(safe_next(next_path).encode("utf-8")).decode("ascii").rstrip("=")
    response.set_cookie(
        STATE_COOKIE, _pack("state", f"{state}:{destination}", STATE_SECONDS), max_age=STATE_SECONDS,
        httponly=True, samesite="lax", secure=settings.cookie_secure(), path="/",
    )
    return state


def read_state(request: Request) -> tuple[str, str] | None:
    """(state, destino) do cookie do login em andamento, ou None."""
    body = _unpack("state", request.cookies.get(STATE_COOKIE))
    if not body or ":" not in body:
        return None
    state, _, destination = body.partition(":")
    try:
        path = base64.urlsafe_b64decode(destination + "=" * (-len(destination) % 4)).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return None
    return state, safe_next(path)


def clear_state(response: Response) -> None:
    response.delete_cookie(STATE_COOKIE, path="/", httponly=True, samesite="lax", secure=settings.cookie_secure())
