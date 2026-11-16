"""Skins no servidor: grava a escolha do jogador direto nas tabelas do plugin WeaponPaints (MariaDB).

O plugin guarda uma linha por arma e por time (2 = TR, 3 = CT); o site grava as duas.
Facas têm dois pontos: o modelo em `wp_player_knife` e a pintura em `wp_player_skins`.
O banco só é tocado quando WP_DB_HOST está configurado; sem isso o recurso fica desligado.
"""
from __future__ import annotations

import time
from threading import RLock

import requests
from fastapi import HTTPException

from . import settings

TEAMS = (2, 3)
KNIVES = {
    500: "weapon_bayonet", 503: "weapon_knife_css", 505: "weapon_knife_flip", 506: "weapon_knife_gut",
    507: "weapon_knife_karambit", 508: "weapon_knife_m9_bayonet", 509: "weapon_knife_tactical",
    512: "weapon_knife_falchion", 514: "weapon_knife_survival_bowie", 515: "weapon_knife_butterfly",
    516: "weapon_knife_push", 517: "weapon_knife_cord", 518: "weapon_knife_canis", 519: "weapon_knife_ursus",
    520: "weapon_knife_gypsy_jackknife", 521: "weapon_knife_outdoor", 522: "weapon_knife_stiletto",
    523: "weapon_knife_widowmaker", 525: "weapon_knife_skeleton", 526: "weapon_knife_kukri",
}
_KNIFE_CLASSES = {v: k for k, v in KNIVES.items()}
CATALOG_TTL = 600

_lock = RLock()
_catalog: dict = {"at": 0.0, "pairs": set()}
_connect = None  # troca nos testes


def enabled() -> bool:
    return settings.wp_config() is not None


def _open():
    if _connect is not None:
        return _connect()
    import pymysql  # import tardio: só precisa existir quando o recurso está ligado

    cfg = settings.wp_config()
    return pymysql.connect(host=cfg["host"], port=cfg["port"], user=cfg["user"], password=cfg["password"],
                           database=cfg["database"], charset="utf8mb4", connect_timeout=5, autocommit=False)


def _pairs() -> set[tuple[int, int]]:
    """Pares (arma, pintura) válidos do catálogo público; evita gravar valores inventados."""
    with _lock:
        if _catalog["pairs"] and time.time() - _catalog["at"] < CATALOG_TTL:
            return _catalog["pairs"]
    url = settings.skins_catalog_url()
    try:
        items = requests.get(url, timeout=10).json()
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


def view(steamid: str | None) -> dict:
    if not enabled():
        return {"enabled": False, "authenticated": bool(steamid), "equipped": [], "knife": None}
    if not steamid:
        return {"enabled": True, "authenticated": False, "equipped": [], "knife": None}

    def run(cur):
        cur.execute("SELECT weapon_defindex, weapon_paint_id, weapon_wear, weapon_seed FROM wp_player_skins "
                    "WHERE steamid = %s AND weapon_team = 2", (steamid,))
        skins = cur.fetchall()
        cur.execute("SELECT knife FROM wp_player_knife WHERE steamid = %s AND weapon_team = 2", (steamid,))
        knife = cur.fetchone()
        return skins, knife

    skins, knife = _db_call(run)
    return {
        "enabled": True, "authenticated": True,
        "equipped": [{"weapon_id": int(w), "paint_id": int(p), "wear": float(wear), "seed": int(seed)}
                     for w, p, wear, seed in skins],
        "knife": knife[0] if knife else None,
    }


def equip(steamid: str | None, weapon_id: int, paint_id: int, wear: float, seed: int) -> dict:
    steamid = _require(steamid)
    if (weapon_id, paint_id) not in _pairs():
        raise ValueError("Essa skin não existe no catálogo.")
    wear = min(max(float(wear), 0.0), 1.0)
    seed = min(max(int(seed), 0), 1000)

    def run(cur):
        for team in TEAMS:
            cur.execute(
                "INSERT INTO wp_player_skins (steamid, weapon_team, weapon_defindex, weapon_paint_id, weapon_wear, weapon_seed) "
                "VALUES (%s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE "
                "weapon_paint_id = VALUES(weapon_paint_id), weapon_wear = VALUES(weapon_wear), weapon_seed = VALUES(weapon_seed)",
                (steamid, team, weapon_id, paint_id, wear, seed))
            if weapon_id in KNIVES:
                cur.execute(
                    "INSERT INTO wp_player_knife (steamid, weapon_team, knife) VALUES (%s, %s, %s) "
                    "ON DUPLICATE KEY UPDATE knife = VALUES(knife)", (steamid, team, KNIVES[weapon_id]))

    _db_call(run)
    return view(steamid)


def unequip(steamid: str | None, weapon_id: int) -> dict:
    steamid = _require(steamid)

    def run(cur):
        cur.execute("DELETE FROM wp_player_skins WHERE steamid = %s AND weapon_defindex = %s AND weapon_team IN (2, 3)",
                    (steamid, weapon_id))
        if weapon_id in KNIVES:
            cur.execute("DELETE FROM wp_player_knife WHERE steamid = %s AND knife = %s", (steamid, KNIVES[weapon_id]))

    _db_call(run)
    return view(steamid)
