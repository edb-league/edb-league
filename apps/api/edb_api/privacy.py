"""Privacidade: cada jogador escolhe o que da conta Steam dele aparece no site.

Por padrão tudo aparece (foto, nome na Steam e horas de CS, sempre só o que a pessoa já deixa público na Steam). Quem
entrou com a Steam pode esconder cada item. O SteamID nunca é mostrado a ninguém, com ou sem esta opção. Sem a tabela
player_privacy (banco local ou migration ainda não aplicada) as escolhas ficam indisponíveis e tudo segue como antes.
"""
from __future__ import annotations

from datetime import datetime, timezone

from .service import LeagueService

TABLE = "player_privacy"
FIELDS = ("hide_avatar", "hide_persona", "hide_hours")


def read_all(service: LeagueService) -> dict[str, dict[str, bool]] | None:
    """{player_id: escolhas}, ou None quando o banco não suporta o recurso."""
    store = service.store
    if not store.cloud:
        return None
    try:
        rows = store._api("GET", TABLE, params={"select": "*"})
    except RuntimeError:
        return None
    return {str(r["player_id"]): {f: bool(r.get(f)) for f in FIELDS} for r in rows}


def hidden(choices: dict[str, dict[str, bool]] | None, player_id: str, field: str) -> bool:
    return bool(choices and choices.get(str(player_id), {}).get(field))


def apply_to_steam(view: dict, choices: dict[str, dict[str, bool]] | None, player_id: str) -> dict:
    """Tira da visão da Steam o que o jogador escondeu."""
    out = dict(view)
    if hidden(choices, player_id, "hide_avatar"):
        out["avatar"] = ""
    if hidden(choices, player_id, "hide_persona"):
        out["persona"] = ""
    if hidden(choices, player_id, "hide_hours"):
        out["hours"], out["note"] = None, ""
    return out


def build_mine(service: LeagueService, player_id: str | None) -> dict:
    choices = read_all(service)
    mine = (choices or {}).get(str(player_id), {}) if player_id else {}
    return {"available": choices is not None and player_id is not None,
            **{f: bool(mine.get(f)) for f in FIELDS}}


def save_mine(service: LeagueService, player_id: str, body: dict[str, bool]) -> dict:
    if read_all(service) is None:
        raise ValueError("As opções de privacidade não estão disponíveis neste servidor.")
    row = {"player_id": str(player_id), **{f: bool(body[f]) for f in FIELDS},
           "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    service.store._upsert(TABLE, row, "player_id")
    service.invalidate()
    return build_mine(service, player_id)
