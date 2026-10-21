"""Configuração lida do ambiente a cada chamada (facilita os testes)."""
from __future__ import annotations

import os
from datetime import date, datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Sao_Paulo")
PLACEHOLDER_PASSWORD = "SUBSTITUA-POR-UMA-SENHA-FORTE"
DEMO_TODAY = date(2026, 11, 10)


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default) or default


def flag(name: str) -> bool:
    return env(name).strip().lower() in ("1", "true", "yes", "sim", "on")


def demo_mode() -> bool:
    return flag("EDB_DEMO")


def supabase_url() -> str:
    return env("SUPABASE_URL")


def supabase_key() -> str:
    return env("SUPABASE_SERVICE_ROLE_KEY")


def steam_key() -> str:
    return env("STEAM_API_KEY")


def admin_password() -> str:
    return env("XINXAS_ADMIN_PASSWORD")


def admin_configured() -> bool:
    password = admin_password()
    return bool(password) and password != PLACEHOLDER_PASSWORD


def session_secret() -> bytes:
    import hashlib

    secret = env("EDB_SESSION_SECRET")
    if secret:
        return secret.encode("utf-8")
    return hashlib.sha256(("edb-session:" + admin_password()).encode("utf-8")).digest()


def allowed_origins() -> list[str]:
    raw = env("EDB_ALLOWED_ORIGINS", "http://localhost:3000")
    return [o.strip().rstrip("/") for o in raw.split(",") if o.strip()]


def cookie_secure() -> bool:
    return flag("EDB_COOKIE_SECURE")


def trust_proxy() -> bool:
    return flag("EDB_TRUST_PROXY")


def today() -> date:
    """Data de hoje em Brasília; EDB_TODAY (AAAA-MM-DD) força um dia fixo."""
    forced = env("EDB_TODAY")
    if forced:
        try:
            return date.fromisoformat(forced)
        except ValueError:
            pass
    if demo_mode():
        return DEMO_TODAY
    return datetime.now(TZ).date()
