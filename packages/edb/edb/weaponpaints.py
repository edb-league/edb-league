"""Leitura e escrita nas tabelas do plugin WeaponPaints (MariaDB). Sem dependências além de um cursor DB-API.

O plugin guarda uma linha por arma e por time (2 = TR, 3 = CT). Facas têm dois pontos: o modelo em
`wp_player_knife` e a pintura em `wp_player_skins`.
"""
from __future__ import annotations

TEAMS = (2, 3)
KNIVES = {
    500: "weapon_bayonet", 503: "weapon_knife_css", 505: "weapon_knife_flip", 506: "weapon_knife_gut",
    507: "weapon_knife_karambit", 508: "weapon_knife_m9_bayonet", 509: "weapon_knife_tactical",
    512: "weapon_knife_falchion", 514: "weapon_knife_survival_bowie", 515: "weapon_knife_butterfly",
    516: "weapon_knife_push", 517: "weapon_knife_cord", 518: "weapon_knife_canis", 519: "weapon_knife_ursus",
    520: "weapon_knife_gypsy_jackknife", 521: "weapon_knife_outdoor", 522: "weapon_knife_stiletto",
    523: "weapon_knife_widowmaker", 525: "weapon_knife_skeleton", 526: "weapon_knife_kukri",
}


def clamp(wear: float, seed: int) -> tuple[float, int]:
    return min(max(float(wear), 0.0), 1.0), min(max(int(seed), 0), 1000)


def equip(cur, steamid: str, weapon_id: int, paint_id: int, wear: float, seed: int) -> None:
    wear, seed = clamp(wear, seed)
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


def unequip(cur, steamid: str, weapon_id: int) -> None:
    cur.execute("DELETE FROM wp_player_skins WHERE steamid = %s AND weapon_defindex = %s AND weapon_team IN (2, 3)",
                (steamid, weapon_id))
    if weapon_id in KNIVES:
        cur.execute("DELETE FROM wp_player_knife WHERE steamid = %s AND knife = %s", (steamid, KNIVES[weapon_id]))


def apply_change(cur, change: dict) -> None:
    """Aplica uma linha de skin_selections (da ponte): `deleted` remove, senão equipa."""
    steamid, weapon_id = str(change["steamid"]), int(change["weapon_id"])
    if change.get("deleted"):
        unequip(cur, steamid, weapon_id)
    else:
        equip(cur, steamid, weapon_id, int(change["paint_id"]), change.get("wear", 0.01), change.get("seed", 0))


def read(cur, steamid: str) -> tuple[list[tuple], tuple | None]:
    cur.execute("SELECT weapon_defindex, weapon_paint_id, weapon_wear, weapon_seed FROM wp_player_skins "
                "WHERE steamid = %s AND weapon_team = 2", (steamid,))
    skins = cur.fetchall()
    cur.execute("SELECT knife FROM wp_player_knife WHERE steamid = %s AND weapon_team = 2", (steamid,))
    return skins, cur.fetchone()
