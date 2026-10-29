"""Login com a Steam (OpenID 2.0), feito do lado do servidor.

A Steam só informa o SteamID de quem entrou. Nada do que o navegador devolve é aceito sem a
confirmação da própria Steam: este módulo confere o formato da resposta e depois pergunta à Steam,
de servidor para servidor, se a assinatura é válida (``check_authentication``).
"""
from __future__ import annotations

import re
import time
from datetime import datetime, timezone
from threading import Lock
from urllib.parse import urlencode

import requests

ENDPOINT = "https://steamcommunity.com/openid/login"
NS = "http://specs.openid.net/auth/2.0"
IDENTIFIER_SELECT = "http://specs.openid.net/auth/2.0/identifier_select"
CLAIMED = re.compile(r"^https://steamcommunity\.com/openid/id/(7656119\d{10})$")
NONCE_MAX_AGE = 5 * 60
# Campos que precisam estar na lista assinada pela Steam; sem isso, alguém poderia inserir um campo solto.
REQUIRED_SIGNED = {"op_endpoint", "claimed_id", "identity", "return_to", "response_nonce", "assoc_handle"}

_seen: dict[str, float] = {}
_lock = Lock()


def reset_state() -> None:
    with _lock:
        _seen.clear()


def login_url(return_to: str, realm: str) -> str:
    """Endereço da Steam para onde o visitante é enviado. A Steam mostra a própria tela de entrada."""
    query = {
        "openid.ns": NS,
        "openid.mode": "checkid_setup",
        "openid.return_to": return_to,
        "openid.realm": realm,
        "openid.identity": IDENTIFIER_SELECT,
        "openid.claimed_id": IDENTIFIER_SELECT,
    }
    return ENDPOINT + "?" + urlencode(query)


def _nonce_ok(nonce: str, now: float) -> bool:
    """O nonce traz a hora da Steam (AAAA-MM-DDTHH:MM:SSZ...). Rejeita velho, futuro distante e repetido."""
    try:
        stamp = datetime.strptime(nonce[:20], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
    except ValueError:
        return False
    if abs(now - stamp) > NONCE_MAX_AGE:
        return False
    with _lock:
        for key in [k for k, until in _seen.items() if until < now]:
            del _seen[key]
        if nonce in _seen:
            return False
        _seen[nonce] = now + 2 * NONCE_MAX_AGE
    return True


def check_with_steam(params: dict[str, str], timeout: float = 6.0) -> bool:
    """Pergunta à Steam se a resposta é autêntica. Qualquer falha de rede conta como "não"."""
    data = {k: v for k, v in params.items() if k.startswith("openid.")}
    data["openid.mode"] = "check_authentication"
    try:
        response = requests.post(ENDPOINT, data=data, timeout=timeout, allow_redirects=False)
        response.raise_for_status()
    except requests.RequestException:
        return False
    lines = {line.strip() for line in response.text.splitlines()}
    return "is_valid:true" in lines


def verify(params: dict[str, str], expected_return_to: str, now: float | None = None) -> str | None:
    """Devolve o SteamID64 de quem entrou, ou None se a resposta não for confiável."""
    now = time.time() if now is None else now
    if params.get("openid.ns") != NS or params.get("openid.mode") != "id_res":
        return None
    if params.get("openid.op_endpoint") != ENDPOINT:
        return None
    if params.get("openid.return_to") != expected_return_to:
        return None
    signed = set(params.get("openid.signed", "").split(","))
    if not REQUIRED_SIGNED <= signed:
        return None
    claimed = CLAIMED.match(params.get("openid.claimed_id", ""))
    if not claimed or params.get("openid.identity") != params.get("openid.claimed_id"):
        return None
    if not _nonce_ok(params.get("openid.response_nonce", ""), now):
        return None
    if not check_with_steam(params):
        return None
    return claimed.group(1)
