"""Montagem dos objetos JSON públicos, reaproveitando as regras de packages/edb."""
from __future__ import annotations

from datetime import timedelta

import pandas as pd

from edb.bagres import bagres_board, premio_henio
from edb.core import TARGET_KPR, enrich, historical_progress
from edb.fixture_cards import basic_team_tables, fixture_overview, match_stat_coverage
from edb.hltv_stats import empty_profile
from edb.league_legacy import hall_of_fame, player_summary
from edb.league_social import MEDALS, achievements, compare_players
from edb.match_cards import match_sort_key, ordered_matches
from edb.season_system import (
    _confront_first_date, _confront_result, _confront_sides, _parse_date, series_format, series_maps,
)
from edb.steam_profile import normalize_steamid64, steam_view
from edb.team_draw import draw_balanced_teams, draw_message

from . import settings
from .service import LeagueService, Snap, display_name, safe_level

RANK_TYPES = ("elite", "superacao", "xp", "bagres")
TITLE_LABELS = {"elite": "MVP", "superacao": "Revelação", "xp": "Xinxa"}
FOCUS = {
    "elite": ("Elite", "Índice Elite", ""),
    "superacao": ("Superação %", "Superação", "%"),
    "xp": ("XP", "XP", ""),
    "bagres": ("ADR", "ADR · pior primeiro", ""),
}
RANK_TITLES = {
    "elite": "Ranking Elite", "superacao": "Ranking Superação",
    "xp": "Ranking XP", "bagres": "Ranking BAGRES",
}
RANK_NOTES = {
    "elite": [
        "Performance absoluta, com índice baseado em kills por round (KPR) e ADR quando há dano disponível. "
        "Conta os 6 melhores mapas de cada jogador na temporada; \"Mapas\" mostra quantos contam do total jogado.",
        "Índice = 100 × (60% × KPR/0,75 + 40% × ADR/75); sem dano, usa KPR. Compare a mesma fonte para maior justiça.",
    ],
    "superacao": [
        "Quanto cada jogador supera a expectativa de KPR para seu nível congelado de 1 a 5 estrelas.",
        "Superação usa os 6 melhores mapas para cada atleta e exige 6 mapas disputados para premiação.",
    ],
    "xp": [
        "Concluir uma partida de pelo menos 8 rounds com KPR igual ou acima da meta rende 100 XP, uma vez a cada semana da temporada.",
        "Presença: +40 XP por mapa; vitória: +20 XP; até 6 mapas na temporada, além de até 100 XP de missão por semana.",
        "Os únicos títulos competitivos oficiais são MVP Elite, Revelação Superação e Xinxa XP. "
        "Os resultados serão homologados após o encerramento.",
    ],
    "bagres": [
        "BAGRES: o menor ADR acumulado da temporada assume a liderança. "
        "Quanto menor o dano médio por round, mais alta a posição neste ranking.",
        "Considera todos os mapas registrados na temporada (não os 6 melhores). "
        "ADR = dano total ÷ rounds individuais. Menos de 2 mapas: provisório. "
        "Rounds inferidos podem afetar o cálculo. O ranking de XP e os títulos oficiais da liga permanecem inalterados.",
    ],
}


class NotFound(LookupError):
    """Recurso inexistente (vira HTTP 404)."""


class Conflict(ValueError):
    """Conflito com dados existentes, como partida duplicada (vira HTTP 409)."""


# Utilidades -------------------------------------------------------------------------
def _none(value):
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def _num(value):
    value = _none(value)
    return None if value is None else float(value)


def _int(value, default=0):
    value = _none(value)
    return default if value is None else int(value)


def _comma(value: float, digits: int = 1, signed: bool = False) -> str:
    text = f"{value:+.{digits}f}" if signed else f"{value:.{digits}f}"
    return text.replace(".", ",")


def _iso(value):
    stamp = pd.to_datetime(value, errors="coerce")
    return None if pd.isna(stamp) else stamp.date().isoformat()


def ref(snap: Snap, player_id) -> dict:
    return {"id": str(player_id), "name": snap.name_of(player_id)}


def player_item(player: dict) -> dict:
    nick = str(player.get("nickname") or "")
    real = str(player.get("real_name") or "").strip() or None
    return {
        "id": str(player["id"]), "nickname": nick, "real_name": real,
        "name": display_name(player), "stars": _int(player.get("stars"), 3),
        "level": safe_level(player), "is_active": bool(player.get("is_active", True)),
    }


def season_info(snap: Snap, row: dict) -> dict:
    number = int(row.get("number", 0))
    today = snap.today
    start, end = _parse_date(row.get("starts_on")), _parse_date(row.get("ends_on"))
    homologated = bool(row.get("homologated_at"))
    progress = None
    if start is None or end is None:
        status = "unknown"
    elif today < start:
        status = "upcoming"
    elif today > end:
        status = "homologated" if homologated else "closed_pending"
    else:
        status = "active"
        progress = {"day": (today - start).days + 1, "total_days": (end - start).days + 1,
                    "remaining": (end - today).days}
    return {
        "number": number, "label": str(row.get("label") or f"Temporada {number}"),
        "starts_on": start.isoformat() if start else None, "ends_on": end.isoformat() if end else None,
        "status": status, "homologated": homologated, "progress": progress,
        "completed_series": snap.completed(number),
    }


def season_by_number(snap: Snap, number: int) -> dict:
    row = snap.season_row(number) or {"number": number, "label": f"Temporada {number}"}
    return season_info(snap, row)


# Fotos da Steam --------------------------------------------------------------------
def build_avatars(service: LeagueService) -> dict[str, str]:
    """{player_id: url da foto} para quem tem SteamID cadastrado. Sem chave ou com a Steam fora do ar: {}."""
    key = settings.steam_key().strip().strip("'\"").strip()
    if not key:
        return {}
    by_steam: dict[str, str] = {}
    for player in service.snap().players:
        steamid = normalize_steamid64(player.get("steamid"))
        if steamid:
            by_steam[steamid] = str(player["id"])
    if not by_steam:
        return {}
    avatars = service.steam_avatars(sorted(by_steam), key)
    return {by_steam[steamid]: url for steamid, url in avatars.items()}


# Quem está logado ------------------------------------------------------------------
def player_for_steamid(snap: Snap, steamid: str) -> dict | None:
    """Jogador cadastrado com esse SteamID64 (aceita os formatos antigos do cadastro)."""
    for player in snap.players:
        if normalize_steamid64(player.get("steamid")) == steamid:
            return player
    return None


def build_me(service: LeagueService, steamid: str | None, admin: bool) -> dict:
    """Dados de quem fez a requisição. Nunca devolve o SteamID."""
    base = {"login_enabled": settings.steam_login_enabled()}
    if steamid is None:
        return {**base, "authenticated": False, "is_admin": False, "player": None, "avatar": None}
    player = player_for_steamid(service.snap(), steamid)
    if player is None and not admin:
        # O cadastro mudou depois do login: sem vínculo, sem sessão útil.
        return {**base, "authenticated": False, "is_admin": False, "player": None, "avatar": None}
    avatar = None
    key = settings.steam_key().strip().strip("'\"").strip()
    if key:
        avatar = service.steam_avatars([steamid], key).get(steamid)
    return {**base, "authenticated": True, "is_admin": admin,
            "player": player_item(player) if player else None, "avatar": avatar}


# Meta ------------------------------------------------------------------------------
def build_meta(service: LeagueService) -> dict:
    snap = service.snap()
    seasons = [season_info(snap, s) for s in sorted(snap.seasons, key=lambda s: int(s["number"]))]
    maps = {str(m.get("map_name")).casefold() for m in snap.matches if m.get("map_name")}
    from datetime import datetime, timezone
    return {
        "demo": service.demo, "cloud": bool(service.store.cloud),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "today": snap.today.isoformat(), "current_season": snap.resolve_season(None),
        "seasons": seasons,
        "counts": {
            "players": len(snap.active_players), "matches": len(snap.matches), "maps": len(maps),
            "kills": sum(_int(s.get("kills")) for s in snap.stats),
        },
    }


# Rankings --------------------------------------------------------------------------
def _ranking_rows(snap: Snap, df: pd.DataFrame, rtype: str) -> list[dict]:
    focus_col = FOCUS[rtype][0]
    rows = []
    for index, r in enumerate(df.to_dict("records"), 1):
        pid = str(r.get("player_id") or "")
        eligible_raw = _none(r.get("Elegível"))
        eligible = True if eligible_raw is None else bool(eligible_raw)
        player = snap.players_by_id.get(pid)
        level = _none(r.get("Nível")) if rtype == "bagres" else None
        if level is None and player is not None:
            level = safe_level(player)
        rows.append({
            "rank": index, "player_id": pid, "name": snap.label(str(r.get("Jogador", ""))),
            "stars": 0 if rtype == "bagres" else _int(r.get("Estrelas")),
            "level": None if level is None else int(level),
            "matches": _int(r.get("Partidas")), "maps_played": (
                _int(r.get("Mapas disputados")) if _none(r.get("Mapas disputados")) is not None else None),
            "kills": _int(r.get("Kills")), "kd": _num(r.get("K/D")), "kpr": _num(r.get("KPR")),
            "adr": _num(r.get("ADR")), "wins": _int(r.get("Vitórias")),
            "elite": None if rtype == "bagres" else _num(r.get("Elite")),
            "superacao": None if rtype == "bagres" else _num(r.get("Superação %")),
            "xp": None if rtype == "bagres" else _num(r.get("XP")),
            "eligible": eligible, "provisional": not eligible, "focus": _num(r.get(focus_col)),
        })
    return rows


def build_ranking(snap: Snap, season: int | None, rtype: str) -> dict:
    if rtype not in RANK_TYPES:
        raise NotFound("Ranking desconhecido.")
    number = snap.resolve_season(season)
    selected = snap.selected_frame(number)
    if rtype == "bagres":
        levels = {str(p["id"]): int(p.get("skill_level") or 5) for p in snap.players}
        board = bagres_board(selected, levels)
    else:
        board = snap.boards(number)[rtype]
    progress = None
    if rtype == "superacao":
        changes = historical_progress(selected)
        progress = [{"name": snap.label(str(r["Jogador"])), "change_pct": float(r["Evolução %"]),
                     "games": int(r["Jogos"])} for r in changes.to_dict("records")]
    _, label, unit = FOCUS[rtype]
    return {
        "season": season_by_number(snap, number), "type": rtype, "title": RANK_TITLES[rtype],
        "focus_label": label, "focus_unit": unit, "rows": _ranking_rows(snap, board, rtype),
        "progress": progress, "notes": RANK_NOTES[rtype],
    }


def _mission_week(snap: Snap, number: int) -> dict | None:
    """Semana de 7 dias da temporada em que estamos (a última, se ela já acabou). Sem datas, sem semana."""
    info = season_by_number(snap, number)
    start, end = _parse_date(info["starts_on"]), _parse_date(info["ends_on"])
    if number < 1 or start is None or end is None:
        return None
    total = ((end - start).days) // 7 + 1
    index = min(max((snap.today - start).days // 7, 0), total - 1)
    first = start + timedelta(days=7 * index)
    # A última semana vai até o fim da temporada (pode ter mais de 7 dias, como no cálculo do XP).
    last = end if index == total - 1 else first + timedelta(days=6)
    return {
        "number": index + 1, "total": total, "starts_on": first.isoformat(), "ends_on": last.isoformat(),
        "days_left": max((last - snap.today).days, 0), "closed": snap.today > end,
    }


def _mission_players(snap: Snap, number: int, week: dict) -> list[dict]:
    """Situação de cada jogador ativo na missão da semana, contando só os mapas que valem para o XP."""
    board = snap.boards(number)["xp"]
    chosen: dict[str, set] = {}
    stars: dict[str, int] = {}
    for r in board.to_dict("records"):
        pid = str(r.get("player_id"))
        chosen[pid] = {str(m) for m in (r.get("Mapas selecionados") or [])}
        stars[pid] = _int(r.get("Estrelas"), 3)
    frame = snap.selected_frame(number)
    first, last = _parse_date(week["starts_on"]), _parse_date(week["ends_on"])
    rows = []
    for player in snap.active_players:
        pid = str(player["id"])
        level_stars = stars.get(pid, _int(player.get("stars"), 3))
        target = TARGET_KPR[max(1, min(5, level_stars))]
        games = []
        if not frame.empty:
            mine = frame[frame["player_id"].astype(str) == pid]
            for g in mine.to_dict("records"):
                played = _parse_date(_iso(g.get("played_at")))
                rounds = _num(g.get("rounds")) or 0
                if played is None or not first <= played <= last or rounds <= 0:
                    continue
                games.append({"match": str(g["match_id"]), "rounds": rounds, "kpr": (_num(g.get("kills")) or 0) / rounds})
        qualifying = [g for g in games if g["kpr"] >= target and g["rounds"] >= 8]
        valid = [g for g in games if g["rounds"] >= 8]
        if any(g["match"] in chosen.get(pid, set()) for g in qualifying):
            status = "done"
        elif qualifying:
            status = "unselected"
        elif games:
            status = "open"
        else:
            status = "none"
        rows.append({
            "player": ref(snap, pid), "level": safe_level(player), "stars": level_stars, "target": target,
            "status": status, "maps_in_week": len(games),
            "best_kpr": round(max((g["kpr"] for g in valid), default=0.0), 3) if valid else None,
        })
    order = {"done": 0, "unselected": 1, "open": 2, "none": 3}
    rows.sort(key=lambda r: (order[r["status"]], -(r["best_kpr"] or 0), r["player"]["name"].casefold()))
    return rows


def build_missions(snap: Snap, season: int | None) -> dict:
    number = snap.resolve_season(season)
    week = _mission_week(snap, number)
    return {
        "targets": [{"stars": stars, "kpr": kpr} for stars, kpr in sorted(TARGET_KPR.items())],
        "xp": build_ranking(snap, season, "xp"),
        "week": week,
        "players": _mission_players(snap, number, week) if week else [],
    }


# Visão geral -----------------------------------------------------------------------
def build_home(snap: Snap, season: int | None) -> dict:
    number = snap.resolve_season(season)
    boards = snap.boards(number)
    selected = snap.selected_frame(number)
    board, superacao, xp = boards["elite"], boards["superacao"], boards["xp"]

    def eligible(df):
        return df[df["Elegível"] == True] if not df.empty else df  # noqa: E712

    def person(row):
        return {"id": str(row["player_id"]), "name": snap.label(str(row["Jogador"]))}

    highlights = []
    elite_rows = eligible(board)
    if not elite_rows.empty:
        r = elite_rows.iloc[0]  # a ordem do ranking já aplica o valor exato e os desempates
        highlights.append({"title": "MVP", "ranking": "elite", "player": person(r),
                           "detail": f"Índice {_comma(float(r['Elite']))} • {int(r['Partidas'])} melhores mapas"})
    else:
        highlights.append({"title": "MVP", "ranking": "elite", "player": None,
                           "detail": "Exige pelo menos 6 mapas"})
    sup_rows = eligible(superacao)
    if not sup_rows.empty:
        r = sup_rows.iloc[0]
        highlights.append({"title": "Revelação", "ranking": "superacao", "player": person(r),
                           "detail": f"{_comma(float(r['Superação %']), 1, True)}% em relação à meta"})
    else:
        highlights.append({"title": "Revelação", "ranking": "superacao", "player": None,
                           "detail": "Aguardando elegíveis"})
    xp_rows = eligible(xp)
    if not xp_rows.empty:
        r = xp_rows.iloc[0]
        highlights.append({"title": "Xinxa", "ranking": "xp", "player": person(r),
                           "detail": f"{int(r['XP'])} XP"})
    else:
        highlights.append({"title": "Xinxa", "ranking": "xp", "player": None,
                           "detail": "Aguardando elegíveis"})

    top = []
    if not board.empty:
        for r in board.head(10).to_dict("records"):
            top.append({"player_id": str(r["player_id"]), "name": snap.label(str(r["Jogador"])),
                        "elite": _num(r["Elite"])})
    roster = [{"id": str(p["id"]), "name": display_name(p), "level": safe_level(p)}
              for p in sorted(snap.active_players, key=lambda p: display_name(p).casefold())]
    return {
        "season": season_by_number(snap, number),
        "counts": {
            "players": len(snap.active_players),
            "matches": int(selected["match_id"].nunique()) if not selected.empty else 0,
            "kills": int(selected["kills"].sum()) if not selected.empty else 0,
            "xp_distributed": int(xp["XP"].sum()) if not xp.empty else 0,
        },
        "highlights": highlights, "top_elite": top, "roster": roster,
    }


# Jogadores -------------------------------------------------------------------------
def build_players(snap: Snap, include_inactive: bool) -> list[dict]:
    source = snap.players if include_inactive else snap.active_players
    return [player_item(p) for p in sorted(source, key=lambda p: display_name(p).casefold())]


def _match_row(r: dict) -> dict:
    won = r.get("won")
    return {
        "match_id": r["match_id"], "date": _iso(r["date"]), "map": r["map"],
        "played_nick": r["played_nick"],
        "result": "win" if won is True else "loss" if won is False else "unknown",
        "kills": r["kills"], "deaths": r["deaths"], "assists": r["assists"], "rounds": r["rounds"],
        "kd": _num(r["kd"]), "kpr": _num(r["kpr"]), "adr": _num(r["adr"]), "rating": _num(r["rating"]),
    }


def _medal(m: dict) -> dict:
    return {k: m[k] for k in ("id", "name", "tier", "description", "metric", "target",
                              "current", "earned", "progress")}


def _avg(values):
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None


def _per_map(records: list[dict]) -> list[dict]:
    groups: dict[str, list[dict]] = {}
    for r in records:
        groups.setdefault(r["map"], []).append(r)
    rows = []
    for name, items in groups.items():
        rounds = sum(r["rounds"] for r in items)
        wins = sum(r["won"] is True for r in items)
        decided = sum(r["won"] is not None for r in items)
        rows.append({
            "map": name, "games": len(items), "wins": wins,
            "win_rate": _num(100 * wins / decided) if decided else None,
            "kpr": _num(sum(r["kills"] for r in items) / rounds) if rounds else None,
            "adr": _num(_avg([r["adr"] for r in items])),
            "rating": _num(_avg([r["rating"] for r in items])),
        })
    return sorted(rows, key=lambda r: (-r["games"], r["map"]))


def _company(snap: Snap, player_id: str, same_team: bool, allowed: set | None = None) -> list[dict]:
    """Rating do jogador nas partidas em que outro jogador esteve no mesmo time (ou no adversário)."""
    mine = {r["match_id"]: r for r in snap.records
            if r["player_id"] == player_id and (allowed is None or str(r["match_id"]) in allowed)}
    others: dict[str, list[dict]] = {}
    for r in snap.records:
        base = mine.get(r["match_id"])
        if r["player_id"] == player_id or base is None or base["won"] is None or r["won"] is None:
            continue
        if (r["won"] == base["won"]) == same_team:
            others.setdefault(r["player_id"], []).append(base)
    rows = [{
        "player": ref(snap, pid), "games": len(items), "rating": _num(_avg([b["rating"] for b in items])),
        "win_rate": _num(100 * sum(b["won"] is True for b in items) / len(items)),
    } for pid, items in others.items()]
    return sorted(rows, key=lambda r: (-r["games"], -(r["rating"] or 0)))[:6]


def _stat_filters(side=None, map_name=None, fmt=None, season=None) -> dict:
    """Normaliza os filtros da aba Estatísticas; valores desconhecidos viram 'sem filtro'."""
    try:
        season = int(season) if season not in (None, "", "todas") else None
    except (TypeError, ValueError):
        season = None
    return {
        "side": str(side).lower() if str(side).lower() in ("t", "ct") else None,
        "map": map_name or None,
        "format": str(fmt).lower() if str(fmt).lower() in ("bo1", "bo3") else None,
        "season": season,
    }


def _advanced(snap: Snap, player_id: str, filters: dict | None = None) -> dict | None:
    f = filters or _stat_filters()
    detailed_all = {str(d["match_id"]) for d in snap.details if str(d["player_id"]) == player_id}
    if not detailed_all:
        return None
    meta = snap.match_meta
    options = {
        "maps": sorted({meta[m]["map"] for m in detailed_all if m in meta and meta[m]["map"]}),
        "formats": sorted({meta[m]["format"] for m in detailed_all if m in meta and meta[m]["format"]}),
        "seasons": sorted({meta[m]["season"] for m in detailed_all if m in meta and meta[m]["season"] is not None}),
    }
    allowed = snap.match_ids_where(f["map"], f["format"], f["season"])
    profile = snap.hltv_for(f["map"], f["format"], f["season"], f["side"]).get(player_id) or empty_profile(f["side"])
    records = [r for r in snap.records if r["player_id"] == player_id and (allowed is None or str(r["match_id"]) in allowed)]
    detailed = detailed_all if allowed is None else detailed_all & allowed
    out = dict(profile)
    out["similar"] = [{"player": ref(snap, s["player_id"]), "similarity": s["similarity"]}
                      for s in profile["similar"] if s["player_id"] in snap.players_by_id]
    out["coverage"] = {"maps_with_demo": len(detailed), "maps_total": len(records)}
    out["maps"] = _per_map(records)
    out["teammates"] = _company(snap, player_id, True, allowed)
    out["opponents"] = _company(snap, player_id, False, allowed)
    out["filters"] = {"applied": f, "options": options}
    return out


def _headline(snap: Snap, player_id: str) -> dict | None:
    """Ratings da demo sem filtro, para o cabeçalho do perfil."""
    profile = snap.hltv.get(player_id)
    if profile is None:
        return None
    return {"rating1": profile["rating"]["rating1"], "rating2": profile["rating"]["rating2"],
            "rating2_t": profile["rating"]["rating2_t"], "rating2_ct": profile["rating"]["rating2_ct"],
            "rating1_t": profile["rating"]["rating1_t"], "rating1_ct": profile["rating"]["rating1_ct"],
            "maps_with_demo": sum(1 for d in snap.details if str(d["player_id"]) == player_id)}


def build_player_detail(service: LeagueService, snap: Snap, player_id: str, filters: dict | None = None) -> dict:
    player = snap.players_by_id.get(str(player_id))
    if player is None:
        raise NotFound("Jogador não encontrado.")
    records = snap.records
    summary = player_summary(str(player["id"]), records)
    best = summary["best"]
    steam = steam_view(player.get("steamid"), settings.steam_key(), service.steam_fetch)
    return {
        "player": player_item(player), "steam": steam,
        "summary": {
            "games": summary["games"], "wins": summary["wins"], "win_rate": _num(summary["win_rate"]),
            "kills": summary["kills"], "deaths": summary["deaths"], "assists": summary["assists"],
            "kd": _num(summary["kd"]), "kpr": _num(summary["kpr"]), "adr": _num(summary["adr"]),
            "best": None if best is None else {
                "kills": best["kills"], "map": best["map"], "date": _iso(best["date"]),
                "match_id": best["match_id"]},
        },
        "matches": [_match_row(r) for r in reversed(summary["matches"])],
        "medals": [_medal(m) for m in achievements(str(player["id"]), records)],
        "headline": _headline(snap, str(player["id"])),
        "advanced": _advanced(snap, str(player["id"]), filters),
    }


# Comparação ------------------------------------------------------------------------
def build_compare(snap: Snap, first_id: str, second_id: str) -> dict:
    for pid in (first_id, second_id):
        if str(pid) not in snap.players_by_id:
            raise NotFound("Jogador não encontrado.")
    comparison = compare_players(first_id, second_id, snap.records)
    fst, snd = comparison["first"], comparison["second"]
    spec = [
        ("games", "Partidas", 0, ""), ("wins", "Vitórias", 0, ""), ("win_rate", "Win rate", 1, "%"),
        ("kills", "Kills", 0, ""), ("kd", "K/D", 2, ""), ("kpr", "KPR", 3, ""),
        ("adr", "ADR estimado", 1, ""), ("assists", "Assistências", 0, ""),
    ]
    metrics = []
    for key, label, decimals, suffix in spec:
        a, b = _num(fst[key]), _num(snd[key])
        better = None
        if a is not None and b is not None:
            better = "first" if a > b else "second" if b > a else "tie"
        metrics.append({"key": key, "label": label, "first": a, "second": b,
                        "decimals": decimals, "suffix": suffix, "better": better})
    h2h = comparison["head_to_head"]
    return {
        "first": player_item(snap.players_by_id[str(first_id)]),
        "second": player_item(snap.players_by_id[str(second_id)]),
        "metrics": metrics, "shared_count": comparison["shared_count"],
        "opponent_games": comparison["opponent_games"], "teammate_games": comparison["teammate_games"],
        "head_to_head": {"first": h2h[str(first_id)], "second": h2h[str(second_id)]},
        "shared": [{
            "match_id": item["match_id"], "date": _iso(item["date"]), "map": item["map"],
            "relation": item["side"],
            "first": {"kills": item["first"]["kills"], "adr": _num(item["first"]["adr"])},
            "second": {"kills": item["second"]["kills"], "adr": _num(item["second"]["adr"])},
        } for item in comparison["shared"]],
    }


# Hall da Fama e medalhas -----------------------------------------------------------
def build_hall(snap: Snap) -> dict:
    records = snap.records
    henio = premio_henio(records, min_maps=2)
    totals: dict = {}
    for row in records:
        entry = totals.setdefault(str(row["player_id"]),
                                  {"id": str(row["player_id"]), "name": row["player_name"], "kills": 0})
        entry["kills"] += row["kills"]
    top = sorted(totals.values(), key=lambda p: (-p["kills"], p["name"]))[:5]
    titles = []
    for item in snap.season_titles:
        pid = str(item["player_id"])
        titles.append({
            "season_number": int(item["season_number"]), "title": TITLE_LABELS.get(item["rank_type"], item["rank_type"]),
            "ranking": item["rank_type"],
            "player": ref(snap, pid) if pid in snap.players_by_id else None,
            "score": round(float(item["score"]), 2),
        })
    titles.sort(key=lambda t: (-t["season_number"], t["title"]))
    return {
        "match_count": len(snap.matches),
        "henio": None if henio is None else {
            "adr": henio["adr"], "min_maps": henio["min_maps"],
            "holders": [{"id": h["id"], "name": h["name"], "maps": h["maps"]} for h in henio["holders"]]},
        "records": [{"title": c["title"], "value": c["value"],
                     "holders": [{"id": h["id"], "name": h["name"]} for h in c["holders"]],
                     "detail": c["detail"]} for c in hall_of_fame(records)],
        "top_kills": [{"player": {"id": p["id"], "name": p["name"]}, "kills": p["kills"]} for p in top],
        "titles": titles,
    }


def build_medals(snap: Snap) -> dict:
    records = snap.records
    by_player = {str(p["id"]): achievements(str(p["id"]), records) for p in snap.active_players}
    earned_total = sum(1 for medals in by_player.values() for m in medals if m["earned"])
    honored = sum(any(m["earned"] for m in medals) for medals in by_player.values())
    catalogue = []
    for rule in MEDALS:
        holders = [ref(snap, p["id"]) for p in snap.active_players
                   if any(m["id"] == rule["id"] and m["earned"] for m in by_player[str(p["id"])])]
        catalogue.append({**{k: rule[k] for k in ("id", "name", "tier", "description", "metric", "target")},
                          "holders": holders})
    return {
        "summary": {"available": len(MEDALS), "honored_players": honored, "tiers": 3,
                    "earned_total": earned_total},
        "medals": catalogue,
    }


# Partidas --------------------------------------------------------------------------
def map_card(match: dict) -> dict:
    info = fixture_overview(match)
    return {
        "id": str(match["id"]), "map": info["map"], "date_label": info["date"],
        "date": _iso(match.get("played_at")), "left": info["left"], "right": info["right"],
        "score_left": info["score_left"], "score_right": info["score_right"],
        "verified": bool(info["verified"]), "winner": info["winner"],
    }


def build_matches(snap: Snap, season: int | None) -> dict:
    number = snap.resolve_season(season)
    games = {str(m["id"]): m for m in snap.matches}
    linked: dict = {}
    for row in snap.bo3_maps:
        linked.setdefault(str(row["series_id"]), []).append(row)
    eligible = sorted((s for s in snap.bo3 if int(s["season_number"]) == number),
                      key=lambda x: int(x["sequence_number"]))
    grouped = {"bo1": [], "bo3": []}
    when: dict[str, tuple] = {}
    for s in eligible:
        sid = str(s["id"])
        maps = sorted(linked.get(sid, []), key=lambda row: int(row["map_number"]))
        fmt = series_format(s)
        minimum = 1 if fmt == "bo1" else 2
        complete = (s.get("status") == "completed" and s.get("winner_side") in ("a", "b")
                    and len(maps) >= minimum)
        status = "FINALIZADA" if complete else ("EM ANDAMENTO" if maps else "AGUARDANDO REGISTRO")
        names = [games[str(m["match_id"])].get("map_name") or "Mapa"
                 for m in maps if str(m.get("match_id")) in games]
        summary = " · ".join(str(x) for x in names) if names else "Mapas ainda não cadastrados"
        if not complete:
            total = 1 if fmt == "bo1" else 3
            summary = f"{len(maps)}/{total} " + ("Mapa" if fmt == "bo1" else "Mapas") + " · " + summary
        result = _confront_result(s, maps, games, fmt, complete)
        left, right, values, left_side, _right_side = _confront_sides(s, result)
        winner = None
        if complete and s.get("winner_side") in ("a", "b"):
            winner = "left" if s["winner_side"] == left_side else "right"
        # A data do confronto é a do primeiro mapa (a mesma do cartão); sem mapa, a data do cadastro.
        first = games.get(str(maps[0].get("match_id"))) if maps else None
        if first is not None:
            stamp = match_sort_key(first)[0]
        else:
            stamp = pd.to_datetime(s.get("played_on"), errors="coerce")
            stamp = pd.Timestamp("1900-01-01") if pd.isna(stamp) else stamp
        when[sid] = (stamp, int(s["sequence_number"]))
        grouped[fmt].append({
            "id": sid, "format": fmt, "date_label": _confront_first_date(s, maps, games),
            "status": status, "complete": bool(complete), "left": left, "right": right,
            "score_left": values[0] if values else None, "score_right": values[1] if values else None,
            "winner": winner, "summary": summary,
            "maps": [map_card(m) for m in series_maps(sid, snap.bo3_maps, snap.matches)],
        })
    # Mais recente primeiro; no mesmo horário, o confronto registrado depois vem antes.
    for items in grouped.values():
        items.sort(key=lambda card: when[card["id"]], reverse=True)
    assigned = {str(m["match_id"]) for m in snap.bo3_maps}
    legacy = [m for m in snap.matches if str(m["id"]) not in assigned]
    return {
        "season": season_by_number(snap, number), "bo1": grouped["bo1"], "bo3": grouped["bo3"],
        "legacy": [map_card(m) for m in ordered_matches(legacy)],
    }


def build_match_detail(snap: Snap, match_id: str) -> dict:
    match = next((m for m in snap.matches if str(m["id"]) == str(match_id)), None)
    if match is None:
        raise NotFound("Partida não encontrada.")
    mid = str(match["id"])
    link = next((m for m in snap.bo3_maps if str(m["match_id"]) == mid), None)
    series = (next((s for s in snap.bo3 if str(s["id"]) == str(link["series_id"])), None)
              if link else None)
    match_stats = [s for s in snap.stats if str(s.get("match_id")) == mid]
    scope = [x for x in snap.scope_stats if str(x.get("match_id")) == mid]
    scope_by_pid = {str(x["player_id"]): x for x in scope}
    frame = enrich(snap.players, [match], match_stats)
    teams, general, aim, utility = [], [], [], []
    if not frame.empty:
        for team in basic_team_tables(match, frame, scope):
            outcome = "win" if team["won"] is True else "loss" if team["won"] is False else "unknown"
            teams.append({
                "name": team["name"], "outcome": outcome, "players": int(team["players"]),
                "kills": int(team["kills"]),
                "rows": [{"player": r["Jogador"], "k": int(r["K"]), "a": int(r["A"]), "d": int(r["D"]),
                          "kd": _num(r["K/D"]), "adr": _num(r["ADR"])}
                         for r in team["table"].to_dict("records")],
            })
        nick_of = {}
        for r in frame.to_dict("records"):
            pid = str(r["player_id"])
            nick = _none(r.get("observed_nickname")) or r.get("nickname") or "Jogador"
            nick_of[pid] = str(nick)
            extra = scope_by_pid.get(pid, {})
            general.append({
                "player": nick_of[pid], "kills": _int(r["kills"]), "deaths": _int(r["deaths"]),
                "assists": _int(r["assists"]), "damage": _num(r["damage"]), "rounds": _int(r["rounds"]),
                "won": r["won"] if r["won"] in (True, False) else None, "rating": _num(r["rating"]),
                "kast": _num(r["kast"]), "open_kills": _num(r["open_kills"]),
                "trade_kills": _num(r["trade_kills"]), "adr_reported": _num(extra.get("adr_reported")),
                "adr_difference": _num(extra.get("adr_difference")),
            })
        aim_keys = ("time_to_kill_seconds", "damage_time_seconds", "aim_accuracy_pct", "rifle_hs_pct",
                    "pistol_hs_pct", "first_bullet_accuracy_pct")
        util_keys = ("flash_assists", "impactful_flash_assists", "enemies_flashed",
                     "total_flash_duration_seconds", "grenade_damage", "smokes_used",
                     "enemies_damaged_fire", "enemies_damaged_he")
        for x in scope:
            pid = str(x["player_id"])
            name = nick_of.get(pid) or (snap.players_by_id.get(pid) or {}).get("nickname") or "Jogador"
            aim.append({"player": name, **{k: _num(x.get(k)) for k in aim_keys}})
            utility.append({"player": name, **{k: _num(x.get(k)) for k in util_keys}})
    coverage = match_stat_coverage(match["id"], snap.stats, snap.scope_stats)
    return {
        "match": map_card(match), "season": int(series["season_number"]) if series else None,
        "series_id": str(series["id"]) if series else None,
        "series_format": series_format(series) if series else None,
        "teams": teams, "general": general, "aim": aim, "utility": utility,
        "coverage": {k: int(v) for k, v in coverage.items()},
        "source": match.get("source") or "Não informada",
        "rounds_total": _int(match.get("rounds_total")) if _none(match.get("rounds_total")) is not None else None,
        "notes": match.get("notes") or None,
    }


# Sorteador -------------------------------------------------------------------------
def build_draw(snap: Snap, player_ids: list[str]) -> dict:
    if len(player_ids) != 10 or len(set(map(str, player_ids))) != 10:
        raise ValueError("Selecione exatamente 10 jogadores diferentes.")
    chosen = []
    for pid in player_ids:
        player = snap.players_by_id.get(str(pid))
        if player is None or not bool(player.get("is_active", True)):
            raise NotFound("Algum jogador selecionado não existe ou não está ativo.")
        chosen.append(player)
    team_a, team_b = draw_balanced_teams(chosen)

    def pack(team):
        return [{"id": str(p["id"]), "name": display_name(p), "level": safe_level(p)} for p in team]

    total_a, total_b = sum(safe_level(p) for p in team_a), sum(safe_level(p) for p in team_b)
    return {"team_a": pack(team_a), "team_b": pack(team_b), "total_a": total_a, "total_b": total_b,
            "gap": abs(total_a - total_b), "message": draw_message(team_a, team_b)}
