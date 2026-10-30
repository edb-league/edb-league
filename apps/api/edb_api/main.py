"""Aplicação FastAPI da EDB LEAGUE. Execução (da raiz): uvicorn --app-dir apps/api edb_api.main:app"""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import settings
from .serializers import CleanJSONResponse
from .views import Conflict, NotFound

log = logging.getLogger("edb.api")

PUBLIC_CACHE = "public, s-maxage=30, stale-while-revalidate=60"


def _warn_about_steam_login() -> None:
    """Se a pessoa começou a configurar o login com a Steam, avisa nos logs o que ainda falta."""
    if not (settings.env("EDB_SESSION_SECRET") or settings.env("EDB_ADMIN_STEAMID") or settings.env("EDB_PUBLIC_URL")):
        return
    for problem in settings.steam_login_problems():
        log.warning("Login com a Steam: %s", problem)


def create_app() -> FastAPI:
    _warn_about_steam_login()
    from .routes_admin import router as admin_router
    from .routes_auth import router as auth_router
    from .routes_public import router as public_router
    from .routes_votes import router as votes_router

    app = FastAPI(title="EDB LEAGUE API", docs_url="/api/docs", openapi_url="/api/openapi.json",
                  default_response_class=CleanJSONResponse)
    app.add_middleware(
        CORSMiddleware, allow_origins=settings.allowed_origins(), allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH"], allow_headers=["Content-Type"],
    )

    @app.middleware("http")
    async def cache_headers(request: Request, call_next):
        response = await call_next(request)
        if "cache-control" not in response.headers:
            path = request.url.path
            private = path.startswith(("/api/admin", "/api/auth", "/api/me", "/api/votes"))
            if request.method == "GET" and path.startswith("/api/") and not private:
                response.headers["Cache-Control"] = PUBLIC_CACHE
            else:
                response.headers["Cache-Control"] = "no-store"
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        return response

    @app.exception_handler(NotFound)
    async def not_found(_: Request, exc: NotFound):
        return CleanJSONResponse({"detail": str(exc)}, status_code=404)

    @app.exception_handler(Conflict)
    async def conflict(_: Request, exc: Conflict):
        return CleanJSONResponse({"detail": str(exc)}, status_code=409)

    @app.exception_handler(ValueError)
    async def bad_value(_: Request, exc: ValueError):
        return CleanJSONResponse({"detail": str(exc)}, status_code=400)

    @app.exception_handler(RuntimeError)
    async def upstream(_: Request, exc: RuntimeError):
        log.warning("Falha em serviço externo: %s", exc)
        return CleanJSONResponse({"detail": str(exc)}, status_code=502)

    @app.exception_handler(StarletteHTTPException)
    async def http_error(_: Request, exc: StarletteHTTPException):
        detail = exc.detail if isinstance(exc.detail, str) else "Requisição não atendida."
        if exc.status_code == 404 and detail == "Not Found":
            detail = "Rota não encontrada."
        return CleanJSONResponse({"detail": detail}, status_code=exc.status_code,
                                 headers=getattr(exc, "headers", None))

    @app.exception_handler(RequestValidationError)
    async def invalid(_: Request, exc: RequestValidationError):
        fields = ", ".join(".".join(str(p) for p in e["loc"][1:]) or str(e["loc"][0]) for e in exc.errors())
        return CleanJSONResponse({"detail": f"Dados inválidos ou ausentes: {fields}."}, status_code=422)

    @app.exception_handler(Exception)
    async def crash(_: Request, exc: Exception):
        log.exception("Erro não tratado")
        return CleanJSONResponse({"detail": "Erro interno. Tente novamente em instantes."}, status_code=500)

    app.include_router(public_router)
    app.include_router(admin_router)
    app.include_router(auth_router)
    app.include_router(votes_router)
    return app


app = create_app()
