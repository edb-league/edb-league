"""Skins no servidor. Dois modos, escolhidos pelo ambiente:

- direto (WP_DB_HOST): a API grava no MariaDB do WeaponPaints. Serve para rodar tudo na mesma máquina.
- ponte (BRIDGE_TOKEN): a API guarda as escolhas na tabela skin_selections e um script no servidor de CS2
  busca as mudanças em /api/skins/bridge/changes (só conexões de saída) e grava no MariaDB.
Sem nenhum dos dois o recurso fica desligado.
"""
from __future__ import annotations

import hmac
import time
from datetime import datetime, timezone
from threading import RLock

import requests
from fastapi import HTTPException

from edb import weaponpaints as wp

from . import settings
from .service import get_service

KNIVES = wp.KNIVES
CATALOG_TTL = 600
BRIDGE_PAGE = 200

_lock = RLock()
_catalog: dict = {"at": 0.0, "pairs": set()}
_connect = None  # troca nos testes


def mode() -> str | None:
    if settings.wp_config() is not None:
        return "direct"
    if settings.env("BRIDGE_TOKEN"):
        return "bridge"
    return None


def enabled() -> bool:
    return mode() is not None


def _open():
    if _connect is not None:
        return _connect()
    import pymysql  # import tardio: só precisa existir no modo direto

    cfg = settings.wp_config()
    return pymysql.connect(host=cfg["host"], port=cfg["port"], user=cfg["user"], password=cfg["password"],
                           database=cfg["database"], charset="utf8mb4", connect_timeout=5, autocommit=False)


def _pairs() -> set[tuple[int, int]]:
    """Pares (arma, pintura) válidos do catálogo público; evita gravar valores inventados."""
    with _lock:
        if _catalog["pairs"] and time.time() - _catalog["at"] < CATALOG_TTL:
            return _catalog["pairs"]
    try:
        items = requests.get(settings.skins_catalog_url(), timeout=10).json()
        pairs = {(int(i["weapon_id"]), int(i["paint_index"])) for i in items}
    except Exception as exc:  # rede, JSON ou formato inesperado
        raise HTTPException(503, "Catálogo de skins indisponível no momento.") from exc
    with _lock:
        _catalog.update(at=time.time(), pairs=pairs)
    return pairs


def _require(steamid: str | None) -> str:
    if not enabled():
        raise HTTPException(503, "Skins no servidor ainda não estão ativadas.")
    if not steamid:
        raise HTTPException(401, "Entre com a Steam para escolher suas skins.")
    return steamid


def _db_call(fn):
    try:
        conn = _open()
    except Exception as exc:
        raise HTTPException(502, "Não consegui falar com o banco de skins.") from exc
    try:
        result = fn(conn.cursor())
        conn.commit()
        return result
    except Exception as exc:
        conn.rollback()
        raise HTTPException(502, "Falha ao gravar no banco de skins.") from exc
    finally:
        conn.close()


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _shape(equipped: list[dict], knife: str | None, gloves: int | None = None) -> dict:
    return {"enabled": True, "authenticated": True, "equipped": equipped, "knife": knife, "gloves": gloves}


def view(steamid: str | None) -> dict:
    if not enabled():
        return {"enabled": False, "authenticated": bool(steamid), "equipped": [], "knife": None, "gloves": None}
    if not steamid:
        return {"enabled": True, "authenticated": False, "equipped": [], "knife": None, "gloves": None}
    if mode() == "bridge":
        rows = [r for r in get_service().store.skin_list(steamid) if not r["deleted"]]
        knives = [r for r in rows if int(r["weapon_id"]) in KNIVES]
        knife = KNIVES[int(max(knives, key=lambda r: str(r["updated_at"]))["weapon_id"])] if knives else None
        gloves = [r for r in rows if int(r["weapon_id"]) in wp.GLOVES]
        glove = int(max(gloves, key=lambda r: str(r["updated_at"]))["weapon_id"]) if gloves else None
        return _shape([{"weapon_id": int(r["weapon_id"]), "paint_id": int(r["paint_id"]),
                        "wear": float(r["wear"]), "seed": int(r["seed"])} for r in rows], knife, glove)
    skins, knife, gloves = _db_call(lambda cur: wp.read(cur, steamid))
    return _shape([{"weapon_id": int(w), "paint_id": int(p), "wear": float(wear), "seed": int(seed)}
                   for w, p, wear, seed in skins], knife[0] if knife else None, int(gloves[0]) if gloves else None)


def _save(steamid: str, weapon_id: int, paint_id: int, wear: float, seed: int, deleted: bool) -> None:
    wear, seed = wp.clamp(wear, seed)
    try:
        get_service().store.skin_put({"steamid": steamid, "weapon_id": weapon_id, "paint_id": paint_id, "wear": wear,
                                      "seed": seed, "deleted": deleted, "updated_at": _now()})
    except RuntimeError as exc:
        raise HTTPException(502, "Falha ao gravar a escolha de skin.") from exc


def equip(steamid: str | None, weapon_id: int, paint_id: int, wear: float, seed: int) -> dict:
    steamid = _require(steamid)
    if (weapon_id, paint_id) not in _pairs():
        raise ValueError("Essa skin não existe no catálogo.")
    if mode() == "bridge":
        _save(steamid, weapon_id, paint_id, wear, seed, False)
    else:
        _db_call(lambda cur: wp.equip(cur, steamid, weapon_id, paint_id, wear, seed))
    return view(steamid)


def unequip(steamid: str | None, weapon_id: int) -> dict:
    steamid = _require(steamid)
    if mode() == "bridge":
        _save(steamid, weapon_id, 0, 0.01, 0, True)
    else:
        _db_call(lambda cur: wp.unequip(cur, steamid, weapon_id))
    return view(steamid)


def bridge_changes(authorization: str, since: str, limit: int) -> dict:
    """Mudanças de skin desde `since`, para o script do servidor de CS2. Exige o token da ponte."""
    token = settings.env("BRIDGE_TOKEN")
    if not token:
        raise HTTPException(503, "A ponte de skins não está ativada.")
    sent = authorization[7:] if authorization.lower().startswith("bearer ") else ""
    if not hmac.compare_digest(sent.encode(), token.encode()):
        raise HTTPException(401, "Token inválido.")
    if since:
        try:
            datetime.fromisoformat(since.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("Parâmetro since inválido.") from exc
    rows = get_service().store.skin_list(None, since or None, min(max(limit, 1), BRIDGE_PAGE))
    changes = [{"steamid": r["steamid"], "weapon_id": int(r["weapon_id"]), "paint_id": int(r["paint_id"]),
                "wear": float(r["wear"]), "seed": int(r["seed"]), "deleted": bool(r["deleted"]),
                "updated_at": str(r["updated_at"])} for r in rows]
    return {"changes": changes, "cursor": changes[-1]["updated_at"] if changes else since}
