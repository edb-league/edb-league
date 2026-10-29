"""Operações administrativas: elenco, confrontos, homologação, importação e backup."""
from __future__ import annotations

import hashlib
import io
import json
from datetime import date

import pandas as pd

from edb import SAMPLE_SCOREBOARD
from edb.bo3_admin import STATS_FIELDS  # noqa: F401  (mantido para referência dos campos)
from edb.confront_registry import prepare_confront_bundle
from edb.core import enrich
from edb.demo_importer import parse_demo_stats, prepare_upload
from edb.season_rankings import has_technical_tie, season_boards
from edb.season_system import season_match_ids

from . import settings, views
from .service import LeagueService, Snap
from .views import Conflict, NotFound, _int, _none, _num, player_item, season_info

MAX_CSV_BYTES = 5 * 1024 * 1024
EXPORTS = {"players": ("jogadores", "players"), "matches": ("partidas", "matches"),
           "stats": ("estatisticas", "stats")}


# Elenco ----------------------------------------------------------------------------
def admin_player(player: dict) -> dict:
    return {**player_item(player), "steamid": str(player.get("steamid") or "") or None}


def _find_player(snap: Snap, player_id: str) -> dict:
    player = snap.players_by_id.get(str(player_id))
    if player is None:
        raise NotFound("Jogador não encontrado.")
    return player


def _refreshed(service: LeagueService, player_id: str) -> dict:
    service.invalidate()
    return admin_player(_find_player(service.snap(), player_id))


def create_player(service: LeagueService, nickname: str, steamid: str | None, level: int) -> dict:
    pid = service.store.save_player(nickname, 3, (steamid or "").strip() or None, skill_level=level)
    return _refreshed(service, pid)


def update_player(service: LeagueService, player_id: str, patch: dict) -> dict:
    existing = _find_player(service.snap(), player_id)
    nickname = patch.get("nickname")
    nickname = existing["nickname"] if nickname is None else nickname
    if "steamid" in patch and patch["steamid"] is not None:
        steamid = patch["steamid"].strip() or None
    else:
        steamid = existing.get("steamid")
    level = patch.get("skill_level")
    level = int(existing.get("skill_level") or 5) if level is None else level
    service.store.save_player(nickname, int(existing["stars"]), steamid, existing["id"], skill_level=level)
    return _refreshed(service, existing["id"])


def set_active(service: LeagueService, player_id: str, active: bool) -> dict:
    existing = _find_player(service.snap(), player_id)
    service.store.set_player_active(existing["id"], active)
    return _refreshed(service, existing["id"])


def overview(service: LeagueService) -> dict:
    snap = service.snap()
    cloud = bool(service.store.cloud)
    pending, open_seasons = [], []
    if cloud:
        for row in sorted(snap.seasons, key=lambda r: int(r["number"])):
            if int(row["number"]) < 1 or row.get("homologated_at"):
                continue
            if row.get("ends_on") and date.fromisoformat(str(row["ends_on"])[:10]) < snap.today:
                pending.append(season_info(snap, row))
            if row.get("starts_on") and row.get("ends_on"):
                open_seasons.append(season_info(snap, row))
    players = sorted(snap.players, key=lambda p: views.display_name(p).casefold())
    return {"cloud": cloud, "players": [admin_player(p) for p in players],
            "pending_seasons": pending, "open_seasons": open_seasons}


# Homologação -----------------------------------------------------------------------
def homologate(service: LeagueService, number: int) -> dict:
    store = service.store
    if not store.cloud:
        raise ValueError("A homologação exige o banco Supabase configurado.")
    snap = service.snap()
    pending = [row for row in snap.seasons
               if int(row["number"]) >= 1 and row.get("ends_on")
               and date.fromisoformat(str(row["ends_on"])[:10]) < snap.today
               and not row.get("homologated_at")]
    if not any(int(row["number"]) == int(number) for row in pending):
        raise NotFound("Essa temporada não está encerrada e pendente de homologação.")
    try:
        series = [r for r in snap.bo3 if int(r["season_number"]) == number]
        if any(r["status"] != "completed" for r in series):
            raise ValueError("Há confrontos incompletos nesta temporada.")
        ids = season_match_ids(number, snap.bo3, snap.bo3_maps)
        frame = snap.frame
        period = frame[frame["match_id"].astype(str).isin(ids)].copy() if not frame.empty else frame.copy()
        frozen = {str(r["player_id"]): int(r["stars"]) for r in snap.frozen_stars
                  if int(r["season_number"]) == number}
        missing = set(period["player_id"].astype(str)) - set(frozen) if not period.empty else set()
        if missing:
            raise ValueError("Existem atletas sem estrelas congeladas; revise antes da homologação.")
        official = season_boards(period, number, frozen)
        any_eligible = any(not df.empty and df["Elegível"].any() for df in official.values())
        for rank_type, df in official.items():
            if has_technical_tie(df, rank_type):
                raise ValueError("Empate técnico no ranking " + rank_type + "; resolva administrativamente.")
        ranks, titles = [], []
        for rank_type, df in official.items():
            for row in json.loads(df.to_json(orient="records")):
                ranks.append({"rank_type": rank_type, "player_id": str(row["player_id"]), "rank_data": row})
            qualified = df[df["Elegível"] == True] if not df.empty else df  # noqa: E712
            if not qualified.empty:
                champion = qualified.iloc[0]
                titles.append({"rank_type": rank_type, "player_id": str(champion["player_id"]),
                               "score": float(champion["__score_precise"])})
        if any_eligible and len(titles) != 3:
            raise ValueError("Os três títulos exigem campeões elegíveis.")
        store._api("POST", "rpc/homologate_edb_season",
                   payload={"p_season": number, "p_rankings": ranks, "p_titles": titles})
    except ValueError as exc:
        raise ValueError("Homologação não realizada: " + str(exc)) from exc
    service.invalidate()
    return {"ok": True}


# Confrontos ------------------------------------------------------------------------
def _open_season(snap: Snap, number: int) -> dict:
    row = next((s for s in snap.seasons if int(s["number"]) == int(number)), None)
    if (row is None or int(row["number"]) < 1 or row.get("homologated_at")
            or not row.get("starts_on") or not row.get("ends_on")):
        raise NotFound("Temporada aberta não encontrada para registrar confrontos.")
    return row


def confront_candidates(service: LeagueService, number: int) -> dict:
    if not service.store.cloud:
        raise ValueError("O registro oficial de confrontos exige o banco Supabase configurado.")
    snap = service.snap()
    season = _open_season(snap, number)
    linked = {str(r["match_id"]) for r in snap.bo3_maps}
    start, end = str(season["starts_on"])[:10], str(season["ends_on"])[:10]
    rosters: dict = {}
    for stat in snap.stats:
        rosters.setdefault(str(stat["match_id"]), []).append(str(stat["player_id"]))
    maps, used = [], set()
    for m in sorted(snap.matches, key=lambda x: (str(x["played_at"]), str(x["id"]))):
        mid = str(m["id"])
        if mid in linked or not start <= str(m["played_at"])[:10] <= end:
            continue
        ids = sorted(set(rosters.get(mid, [])))
        used.update(ids)
        maps.append({
            "id": mid, "played_at": str(m["played_at"])[:10], "map_name": str(m.get("map_name") or "Mapa"),
            "label": f"{str(m['played_at'])[:10]} · {m.get('map_name') or 'Mapa'} · {mid[:12]}",
            "rounds_total": _int(m.get("rounds_total")) if _none(m.get("rounds_total")) is not None else None,
            "team_a_score": _int(m.get("team_a_score")) if _none(m.get("team_a_score")) is not None else None,
            "team_b_score": _int(m.get("team_b_score")) if _none(m.get("team_b_score")) is not None else None,
            "player_ids": ids,
        })
    players = sorted((views.ref(snap, pid) for pid in used if pid in snap.players_by_id),
                     key=lambda r: r["name"].casefold())
    return {"season": season_info(snap, season), "maps": maps, "players": players}


def register_confront(service: LeagueService, req: dict) -> dict:
    if not service.store.cloud:
        raise ValueError("O registro oficial de confrontos exige o banco Supabase configurado.")
    snap = service.snap()
    season = _open_season(snap, req["season"])
    scores = {mid: (int(pair[0]), int(pair[1])) for mid, pair in req["scores"].items()}
    missing = [mid for mid in req["match_ids"] if mid not in scores]
    if missing:
        raise ValueError("Informe o placar de todos os mapas selecionados.")
    payload = prepare_confront_bundle(
        season, req["format"], req["match_ids"], snap.matches, snap.stats,
        req["team_a_ids"], scores, req["team_a_name"], req["team_b_name"])
    service.store._api("POST", "rpc/register_edb_confronto", payload={"p_bundle": payload})
    service.invalidate()
    return {"ok": True}


# Importação ------------------------------------------------------------------------
class _Upload:
    """Adapta UploadFile ao objeto simples esperado por prepare_upload."""

    def __init__(self, upload):
        self.name = upload.filename or ""
        self._file = upload.file

    def __getattr__(self, item):
        return getattr(self._file, item)


def _opt_int(value):
    value = _none(value)
    if value is None or str(value).strip() == "":
        return None
    return max(0, int(float(value)))


def _opt_float(value):
    value = _none(value)
    if value is None or str(value).strip() == "":
        return None
    return float(value)


def _won(value):
    if value in (True, 1, "1", "true", "True"):
        return True
    if value in (False, 0, "0", "false", "False"):
        return False
    return None


def normalize_player(raw: dict) -> dict:
    steam = _none(raw.get("steamid"))
    steam = "" if steam is None else str(steam).strip()
    if steam.lower() in ("nan", "none"):
        steam = ""
    return {
        "nickname": str(_none(raw.get("nickname")) or "").strip(), "steamid": steam,
        "kills": _opt_int(raw.get("kills")) or 0, "deaths": _opt_int(raw.get("deaths")) or 0,
        "assists": _opt_int(raw.get("assists")) or 0, "damage": _opt_int(raw.get("damage")),
        "rounds": _opt_int(raw.get("rounds")) or 0, "headshots": _opt_int(raw.get("headshots")) or 0,
        "plants": _opt_int(raw.get("plants")) or 0, "defuses": _opt_int(raw.get("defuses")) or 0,
        "rating": _opt_float(raw.get("rating")), "kast": _opt_float(raw.get("kast")),
        "open_kills": _opt_int(raw.get("open_kills")), "trade_kills": _opt_int(raw.get("trade_kills")),
        "won": _won(_none(raw.get("won"))),
    }


def _read_csv_text(text: str) -> pd.DataFrame:
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if "nickname" in line and "kills" in line), 0)
    return pd.read_csv(io.StringIO("\n".join(lines[start:])), dtype={"steamid": str})


def _is_invalid_demo(source: str, players: list[dict]) -> bool:
    return (str(source).startswith("Demo da xplay")
            and sum(int(p.get("kills") or 0) for p in players) == 0
            and sum(int(p.get("deaths") or 0) for p in players) == 0)


def preview_import(service: LeagueService, method: str, upload) -> dict:
    if method == "sample":
        df = _read_csv_text(SAMPLE_SCOREBOARD.read_text(encoding="utf-8"))
        fingerprint, map_name, rounds = "scope_1648990866439220", "Inferno", 17
        records = df.where(pd.notna(df), None).to_dict("records")
        warnings = ["Dado transcrito do print do SCOPE.GG; rounds estimados, não validados pela demo."]
        source = "SCOPE.GG, transcrição do print"
    elif method == "csv":
        if upload is None:
            raise ValueError("Envie um arquivo CSV.")
        blob = upload.file.read(MAX_CSV_BYTES + 1)
        if len(blob) > MAX_CSV_BYTES:
            raise ValueError("O CSV excede 5 MB.")
        try:
            df = pd.read_csv(io.BytesIO(blob), dtype={"steamid": str})
        except Exception as exc:
            raise ValueError("Erro no CSV: " + str(exc)) from exc
        required = {"nickname", "kills", "deaths", "assists", "rounds"}
        if not required.issubset(df.columns):
            raise ValueError("Colunas obrigatórias: " + ", ".join(sorted(required)))
        fingerprint = "csv_" + hashlib.sha256(blob).hexdigest()
        map_name, rounds = "Não informado", int(df["rounds"].max())
        records = df.where(pd.notna(df), None).to_dict("records")
        warnings = ["Dados recebidos por CSV: confirme o placar antes de salvar."]
        source = "CSV de placar"
    elif method == "demo":
        if upload is None:
            raise ValueError("Envie o arquivo da demo (.dem, .dem.gz ou .gz).")
        folder = None
        try:
            folder, path, fingerprint = prepare_upload(_Upload(upload))
            result = parse_demo_stats(path, fingerprint)
        except Exception as exc:
            raise ValueError("Não foi possível processar a demo: " + str(exc)) from exc
        finally:
            if folder:
                folder.cleanup()
        fingerprint, map_name, rounds = result.fingerprint, result.map_name, result.rounds_total
        records, warnings, source = result.players, list(result.warnings), "Demo da xplay / demoparser2"
    else:
        raise ValueError("Origem de dados desconhecida. Use demo, csv ou sample.")
    players = [normalize_player(r) for r in records]
    return {
        "fingerprint": fingerprint, "map": map_name, "rounds_total": int(rounds), "source": source,
        "warnings": warnings, "players": players,
        "duplicate": bool(service.store.match_exists(fingerprint)),
        "invalid_stats": _is_invalid_demo(source, players),
    }


def commit_import(service: LeagueService, body: dict) -> dict:
    store = service.store
    players = [normalize_player(p) for p in body["players"]]
    if _is_invalid_demo(body["source"], players):
        raise ValueError("Esta prévia não tem kills nem mortes: erro de leitura da demo. "
                         "Descarte a prévia e analise o arquivo de novo.")
    nicknames = [p["nickname"] for p in players]
    if not all(nicknames):
        raise ValueError("Todos os participantes devem ter nicknames.")
    if len({n.casefold() for n in nicknames}) != len(nicknames):
        raise ValueError("Não pode haver nicknames duplicados na mesma partida.")
    if len(players) < 2:
        raise ValueError("A partida precisa ter pelo menos dois participantes.")
    try:
        played = date.fromisoformat(str(body["played_at"])[:10])
    except ValueError as exc:
        raise ValueError("Informe a data real da partida (AAAA-MM-DD).") from exc
    total = int(body["rounds_total"])
    if not 1 <= total <= 80:
        raise ValueError("Os rounds totais devem ficar entre 1 e 80.")
    fingerprint = str(body["fingerprint"]).strip()
    if not fingerprint:
        raise ValueError("Identificador da partida ausente.")
    if store.match_exists(fingerprint):
        raise Conflict("Este ID de partida já está salvo. Importação duplicada bloqueada.")
    winners = {w.strip() for w in body.get("winners", [])}
    existing = store.players()
    lines = []
    for p in players:
        nick, sid = p["nickname"], p["steamid"] or None
        old = next((x for x in existing
                    if (sid and x.get("steamid") == sid) or x["nickname"].casefold() == nick.casefold()), None)
        pid = store.save_player(nick, int(old["stars"]) if old else 3, sid)
        won = True if nick in winners else (False if winners else p["won"])
        lines.append({
            "match_id": fingerprint, "player_id": pid, "kills": p["kills"], "deaths": p["deaths"],
            "assists": p["assists"], "damage": p["damage"], "rounds": p["rounds"], "won": won,
            "headshots": p["headshots"], "plants": p["plants"], "defuses": p["defuses"],
            "rating": p["rating"], "kast": p["kast"], "open_kills": p["open_kills"],
            "trade_kills": p["trade_kills"], "observed_nickname": nick,
        })
    store.save_match({"id": fingerprint, "played_at": str(played), "map_name": body["map_name"],
                      "source": body["source"], "rounds_total": total, "notes": body.get("note") or ""}, lines)
    service.invalidate()
    return {"ok": True, "match_id": fingerprint}


# Backup ----------------------------------------------------------------------------
def export_csv(service: LeagueService, kind: str) -> tuple[bytes, str]:
    if kind not in EXPORTS:
        raise NotFound("Exportação desconhecida.")
    label, method = EXPORTS[kind]
    rows = getattr(service.store, method)()
    return pd.DataFrame(rows).to_csv(index=False).encode("utf-8-sig"), f"xinxas_{label}.csv"
