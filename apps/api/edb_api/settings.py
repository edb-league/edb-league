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


def password_login_enabled() -> bool:
    """Entrada por senha: só vale com uma senha de verdade configurada."""
    password = admin_password()
    return bool(password) and password != PLACEHOLDER_PASSWORD


def steam_login_enabled() -> bool:
    """Login com a Steam exige um segredo de sessão próprio; sem ele, ficaria preso à senha do admin."""
    return len(env("EDB_SESSION_SECRET").strip()) >= 16


def admin_steamid() -> str:
    """SteamID64 da única conta com acesso à administração pela Steam (EDB_ADMIN_STEAMID)."""
    from edb.steam_profile import normalize_steamid64

    return normalize_steamid64(env("EDB_ADMIN_STEAMID")) or ""


def admin_configured() -> bool:
    return password_login_enabled() or (steam_login_enabled() and bool(admin_steamid()))


def steam_login_problems() -> list[str]:
    """Motivos pelos quais o login com a Steam está desligado ou incompleto (sem expor nenhum valor)."""
    problems = []
    secret = env("EDB_SESSION_SECRET").strip()
    if not steam_login_enabled():
        problems.append(
            f"EDB_SESSION_SECRET precisa ter pelo menos 16 caracteres (hoje tem {len(secret)}); "
            "sem isso o login com a Steam fica desligado."
        )
    raw_admin = env("EDB_ADMIN_STEAMID").strip()
    if raw_admin and not admin_steamid():
        problems.append("EDB_ADMIN_STEAMID não é um SteamID64 válido (17 dígitos, começando por 7656119).")
    if not raw_admin:
        problems.append("EDB_ADMIN_STEAMID não está definido: ninguém acessa a Administração pela Steam.")
    return problems


def public_url() -> str:
    """Endereço público do site (o domínio que o visitante vê), usado no retorno do login da Steam."""
    configured = env("EDB_PUBLIC_URL").strip().rstrip("/")
    if configured:
        return configured
    origins = allowed_origins()
    return origins[0] if origins else "http://localhost:3000"


def session_secret() -> bytes:
    import hashlib

    secret = env("EDB_SESSION_SECRET").strip()
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
