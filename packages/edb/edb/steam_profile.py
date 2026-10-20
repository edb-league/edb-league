"""Foto e horas de CS de cada jogador, lidas da Steam a partir do SteamID cadastrado.

A chave da Steam Web API (STEAM_API_KEY) fica só nos Secrets do Streamlit e nunca
é registrada em mensagens de erro. Sem chave, sem SteamID ou com perfil privado o
site continua funcionando, mostrando a silhueta cinza.
"""
from __future__ import annotations

import re
from urllib.parse import urlparse

import requests

STEAM64_BASE = 76561197960265728
CS_APP_ID = 730  # CS2 e CS:GO compartilham o mesmo appid
SUMMARY_URL = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
OWNED_GAMES_URL = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/"
AVATAR_HOSTS = ("steamstatic.com", "akamaihd.net")


class SteamUnavailable(Exception):
    """A Steam não respondeu; nunca carrega a URL nem a chave.

    `reason` é só um código curto: key (chave recusada), limit (muitas consultas),
    timeout, network, http ou response.
    """

    def __init__(self, reason="network"):
        super().__init__("Steam indisponível")
        self.reason = reason


def normalize_steamid64(value):
    """Aceita SteamID64, STEAM_0:Y:Z e [U:1:N]; devolve o SteamID64 ou None."""
    text = str(value or "").strip()
    if re.fullmatch(r"7656119\d{10}", text):
        return text
    legacy = re.fullmatch(r"STEAM_[0-5]:([01]):(\d+)", text, re.IGNORECASE)
    if legacy:
        account = int(legacy.group(2)) * 2 + int(legacy.group(1))
    else:
        modern = re.fullmatch(r"\[?U:1:(\d+)\]?", text, re.IGNORECASE)
        if not modern:
            return None
        account = int(modern.group(1))
    return str(STEAM64_BASE + account) if account > 0 else None


def safe_avatar_url(url):
    """Só aceita imagens https servidas pelos domínios da Steam."""
    try:
        parsed = urlparse(str(url or ""))
    except ValueError:
        return ""
    host = (parsed.hostname or "").lower()
    if parsed.scheme == "https" and any(
        host == domain or host.endswith("." + domain) for domain in AVATAR_HOSTS
    ):
        return str(url)
    return ""


def fetch_steam_profile(steamid64, api_key, session=None, timeout=6):
    """Consulta foto, nome e minutos de CS. Levanta SteamUnavailable em falhas."""
    get = (session or requests).get
    try:
        summary = get(SUMMARY_URL, params={"key": api_key, "steamids": steamid64},
                      timeout=timeout)
        summary.raise_for_status()
        players = (summary.json().get("response") or {}).get("players") or []
        owned = get(OWNED_GAMES_URL, params={
            "key": api_key, "steamid": steamid64, "format": "json",
            "include_played_free_games": 1, "appids_filter[0]": CS_APP_ID,
        }, timeout=timeout)
        owned.raise_for_status()
        games = (owned.json().get("response") or {}).get("games") or []
    except requests.HTTPError as exc:
        status = getattr(getattr(exc, "response", None), "status_code", None)
        reason = "key" if status in (401, 403) else "limit" if status == 429 else "http"
        raise SteamUnavailable(reason) from None
    except requests.Timeout:
        raise SteamUnavailable("timeout") from None
    except requests.RequestException:
        raise SteamUnavailable("network") from None
    except (ValueError, AttributeError):
        raise SteamUnavailable("response") from None
    profile = players[0] if players else {}
    cs = next((g for g in games if int(g.get("appid", 0)) == CS_APP_ID), None)
    return {
        "found": bool(profile),
        "persona": str(profile.get("personaname") or ""),
        "avatar": safe_avatar_url(profile.get("avatarfull")),
        "hours": round(int(cs.get("playtime_forever", 0)) / 60, 1) if cs else None,
        "hours_visible": cs is not None,
    }


ERROR_NOTES = {
    "key": "Chave da Steam recusada pelo servidor da Steam",
    "limit": "A Steam limitou as consultas; tente em alguns minutos",
}


def steam_view(steamid_raw, api_key, fetch):
    """Estado exibido no banner: vinculado, sem Steam ou indisponível."""
    api_key = str(api_key or "").strip().strip("'\"").strip()
    empty = {"state": "", "avatar": "", "persona": "", "hours": 0.0, "note": ""}
    if not str(steamid_raw or "").strip():
        return {**empty, "state": "unlinked"}
    steamid64 = normalize_steamid64(steamid_raw)
    if steamid64 is None:
        return {**empty, "state": "invalid", "note": "SteamID inválido no cadastro"}
    if not api_key:
        return {**empty, "state": "no_key", "hours": None,
                "note": "Steam ainda não conectada ao site"}
    try:
        data = fetch(steamid64, api_key)
    except SteamUnavailable as exc:
        return {**empty, "state": "error", "hours": None,
                "note": ERROR_NOTES.get(getattr(exc, "reason", ""),
                                        "Steam indisponível no momento")}
    if not data.get("found", True):
        return {**empty, "state": "notfound", "hours": None,
                "note": "Perfil não encontrado na Steam; confira o SteamID"}
    visible = data.get("hours_visible")
    return {**empty, "state": "linked", "avatar": data.get("avatar", ""),
            "persona": data.get("persona", ""),
            "hours": data.get("hours") if visible else None,
            "note": "" if visible else "Horas de jogo não públicas na Steam"}
