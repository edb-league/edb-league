"""Sessão do administrador: cookie assinado, limite de tentativas e checagem de Origin."""
from __future__ import annotations

import hashlib
import hmac
import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, Request, Response

from . import settings

COOKIE_NAME = "edb_admin"
SESSION_SECONDS = 8 * 60 * 60
MAX_FAILURES = 5
WINDOW_SECONDS = 15 * 60

_failures: dict[str, deque] = defaultdict(deque)
_lock = Lock()


def now() -> float:
    """Relógio isolado para que os testes possam avançar o tempo."""
    return time.time()


def reset_state() -> None:
    with _lock:
        _failures.clear()


def _sign(expiry: str) -> str:
    return hmac.new(settings.session_secret(), expiry.encode("ascii"), hashlib.sha256).hexdigest()


def make_token(issued_at: float | None = None) -> str:
    expiry = str(int((issued_at if issued_at is not None else now()) + SESSION_SECONDS))
    return expiry + "." + _sign(expiry)


def verify_token(token: str | None) -> bool:
    if not token or "." not in token or not settings.password_login_enabled():
        return False
    expiry, _, signature = token.partition(".")
    if not expiry.isdigit() or not hmac.compare_digest(signature, _sign(expiry)):
        return False
    return int(expiry) > now()


def client_ip(request: Request) -> str:
    if settings.trust_proxy():
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "desconhecido"


def _recent(ip: str) -> deque:
    attempts = _failures[ip]
    limit = now() - WINDOW_SECONDS
    while attempts and attempts[0] < limit:
        attempts.popleft()
    return attempts


def ensure_not_locked(ip: str) -> None:
    with _lock:
        if len(_recent(ip)) >= MAX_FAILURES:
            raise HTTPException(
                429, "Muitas tentativas incorretas. Aguarde alguns minutos e tente de novo."
            )


def register_failure(ip: str) -> None:
    with _lock:
        _recent(ip).append(now())


def clear_failures(ip: str) -> None:
    with _lock:
        _failures.pop(ip, None)


def check_password(candidate: str) -> bool:
    return settings.password_login_enabled() and hmac.compare_digest(
        candidate.encode("utf-8"), settings.admin_password().encode("utf-8")
    )


def set_cookie(response: Response) -> None:
    response.set_cookie(
        COOKIE_NAME, make_token(), max_age=SESSION_SECONDS, httponly=True,
        samesite="lax", secure=settings.cookie_secure(), path="/",
    )


def clear_cookie(response: Response) -> None:
    response.delete_cookie(
        COOKIE_NAME, path="/", httponly=True, samesite="lax", secure=settings.cookie_secure()
    )


def check_origin(request: Request) -> None:
    """Bloqueia requisições de escrita vindas de outro site.

    Com Origin presente, ele precisa estar na lista permitida. Sem Origin, só se
    recusa quando o navegador declara Sec-Fetch-Site cross-site. Clientes que não são
    navegadores não carregam o cookie, então não há risco de CSRF.
    """
    origin = request.headers.get("origin")
    if origin:
        if origin.rstrip("/") not in settings.allowed_origins():
            raise HTTPException(403, "Origem não autorizada para esta operação.")
        return
    if request.headers.get("sec-fetch-site", "").lower() == "cross-site":
        raise HTTPException(403, "Origem não autorizada para esta operação.")


def steam_admin(request: Request) -> bool:
    """True quando quem fez a requisição entrou com a Steam na conta do administrador."""
    from . import identity

    admin = settings.admin_steamid()
    steamid = identity.session_steamid(request)
    return bool(admin) and steamid is not None and hmac.compare_digest(steamid, admin)


def is_admin(request: Request) -> bool:
    return verify_token(request.cookies.get(COOKIE_NAME)) or steam_admin(request)


def require_admin(request: Request) -> None:
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        check_origin(request)
    if not settings.admin_configured():
        raise HTTPException(
            503, "Administração bloqueada: configure EDB_ADMIN_STEAMID (e EDB_SESSION_SECRET) ou XINXAS_ADMIN_PASSWORD no servidor."
        )
    if not is_admin(request):
        raise HTTPException(401, "Sessão de administrador ausente ou expirada. Entre novamente.")
