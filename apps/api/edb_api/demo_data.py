"""Dados sintéticos e determinísticos para desenvolvimento e testes (EDB_DEMO=1).

Jogadores, apelidos e partidas são fictícios. Nada aqui vem da liga real. As datas partem
de 19/10/2026 (início da Temporada 1) para que os resultados sejam sempre os mesmos.
"""
from __future__ import annotations

import hashlib
import json
import random
import uuid
from datetime import date, timedelta
from threading import RLock

from edb.storage import Store

NAMESPACE = uuid.UUID("5d1c0f4e-7a3b-4c52-9d10-0e6b2f4a9c11")

PLAYERS = [
    # nickname, nome real, nível 1 a 10, estrelas 1 a 5, steamid
    ("Falcão", "Rafael", 9, 5, "76561198000000101"),
    ("Tubarão", "Davi", 8, 5, None),
    ("Mirage", None, 7, 4, None),
    ("Nebulosa", "Caio", 7, 4, "76561198000000104"),
    ("Cobra", None, 6, 3, None),
    ("Lince", "Bruno", 6, 3, None),
    ("Trovão", None, 5, 3, None),
    ("Faísca", "Igor", 5, 3, "76561198000000108"),
    ("Vulcão", None, 4, 2, None),
    ("Gaivota", "Lucas", 4, 2, None),
    ("Raposa", None, 3, 1, None),
    ("Jaguar", "Mateus", 3, 1, None),
    ("Orca", None, 6, 3, None),
    ("Pantera", None, 5, 3, None),
]
INACTIVE = {12, 13}
R1 = list(range(0, 10))
R2 = list(range(2, 12))
R3 = list(range(4, 14))

MAPS = ["Inferno", "Mirage", "Ancient", "Nuke", "Overpass", "Anubis", "Dust2", "Vertigo", "Train"]
SOURCE_DEMO = "Demo da xplay / demoparser2"
SOURCE_SCOPE = "SCOPE.GG"


def _pid(index: int) -> str:
    return str(uuid.uuid5(NAMESPACE, PLAYERS[index][0]))


def _mid(label: str) -> str:
    return hashlib.sha1(("edb-demo:" + label).encode()).hexdigest()


def _make_players() -> list[dict]:
    rows = []
    for index, (nick, real, level, stars, steam) in enumerate(PLAYERS):
        rows.append({
            "id": _pid(index), "nickname": nick, "real_name": real, "steamid": steam,
            "stars": stars, "skill_level": level, "is_active": index not in INACTIVE,
            "created_at": "2026-09-01T12:00:00+00:00",
        })
    return rows


def _stats_for(rng, match_id, roster, team_a, a_score, b_score, source_scope=False):
    rounds = a_score + b_score
    lines, extras = [], []
    for index in roster:
        level = PLAYERS[index][2]
        won = (index in team_a) == (a_score > b_score)
        kpr = min(1.5, max(0.2, 0.42 + 0.05 * level + rng.gauss(0, 0.08) + (0.03 if won else -0.03)))
        kills = max(0, round(kpr * rounds))
        deaths = max(1, round(rounds * (0.56 if won else 0.74) + rng.gauss(0, 1.5)))
        adr = max(25.0, 38 + 6.5 * level + rng.gauss(0, 9))
        damage = int(adr * rounds)
        lines.append({
            "match_id": match_id, "player_id": _pid(index), "kills": kills, "deaths": deaths,
            "assists": rng.randint(0, 7), "damage": damage, "rounds": rounds, "won": won,
            "headshots": int(kills * rng.uniform(0.3, 0.6)), "plants": rng.randint(0, 2),
            "defuses": rng.randint(0, 1), "rating": round(0.5 + kpr * 0.8, 2),
            "kast": round(rng.uniform(55, 82), 1), "open_kills": rng.randint(0, 4),
            "trade_kills": rng.randint(0, 3), "observed_nickname": PLAYERS[index][0],
        })
        if source_scope:
            reported = round(damage / rounds + rng.uniform(-1.5, 1.5), 1)
            extras.append({
                "match_id": match_id, "player_id": _pid(index), "adr_reported": reported,
                "adr_difference": round(reported - damage / rounds, 1),
                "time_to_kill_seconds": round(rng.uniform(0.35, 0.9), 2),
                "damage_time_seconds": round(rng.uniform(0.6, 1.4), 2),
                "aim_accuracy_pct": round(rng.uniform(18, 34), 1),
                "rifle_hs_pct": round(rng.uniform(25, 60), 1),
                "pistol_hs_pct": round(rng.uniform(10, 50), 1),
                "first_bullet_accuracy_pct": round(rng.uniform(15, 45), 1),
                "flash_assists": rng.randint(0, 4), "impactful_flash_assists": rng.randint(0, 3),
                "enemies_flashed": rng.randint(0, 12), "total_flash_duration_seconds": round(rng.uniform(0, 30), 1),
                "grenade_damage": rng.choice([0, 12, 34, 58, 87, 120, 215]),
                "smokes_used": rng.randint(0, 8), "enemies_damaged_fire": rng.randint(0, 4),
                "enemies_damaged_he": rng.randint(0, 5),
            })
    return lines, extras


def build_demo_data() -> dict:
    rng = random.Random(20261019)
    players = _make_players()
    matches, stats, scope = [], [], []
    series, series_maps, series_players = [], [], []
    start = date(2026, 10, 19)

    def add_series(label, season, seq, fmt, roster, maps, names=("PT", "PL"), status="completed",
                   played_on=None, first_day=0):
        """maps: lista de (mapa, dia_relativo, placar_a, placar_b, usar_scope)."""
        team_a = set(roster[:5]) if names[0] == "PT" else set(roster[5:])
        # O time A do registro e sempre o primeiro grupo de cinco jogadores.
        team_a = set(roster[:5])
        sid = "ser-" + label
        wins = {"a": 0, "b": 0}
        for number, (map_name, day, a, b, with_scope) in enumerate(maps, 1):
            match_id = _mid(f"{label}-{number}")
            played = (start + timedelta(days=day)).isoformat() if season >= 1 else (
                date(2026, 10, 3) + timedelta(days=day)).isoformat()
            lines, extras = _stats_for(rng, match_id, roster, team_a, a, b, with_scope)
            stats.extend(lines)
            scope.extend(extras)
            matches.append({
                "id": match_id, "played_at": played, "map_name": map_name,
                "source": SOURCE_SCOPE if with_scope else SOURCE_DEMO, "rounds_total": a + b,
                "notes": "Registro sintético de demonstração." if number == 1 else "",
                "team_a_name": names[0], "team_b_name": names[1],
                "team_a_score": a, "team_b_score": b, "result_verified": True,
            })
            side = "a" if a > b else "b"
            wins[side] += 1
            series_maps.append({"series_id": sid, "match_id": match_id, "map_number": number, "winner_side": side})
        need = 1 if fmt == "bo1" else 2
        winner = "a" if wins["a"] >= need else "b" if wins["b"] >= need else None
        if status != "completed":
            winner = None
        first_played = None
        if maps:
            first_played = matches[-len(maps)]["played_at"]
        series.append({
            "id": sid, "season_number": season, "sequence_number": seq, "match_format": fmt,
            "status": status, "winner_side": winner, "team_a_name": names[0], "team_b_name": names[1],
            "played_on": played_on or first_played,
        })
        for index in roster:
            series_players.append({"series_id": sid, "player_id": _pid(index),
                                   "team_side": "a" if index in team_a else "b"})

    # Temporada 0 (experimental, homologada): duas BO3.
    add_series("t0-01", 0, 1, "bo3", R1, [
        ("Mirage", 0, 13, 9, False), ("Inferno", 0, 11, 13, False), ("Nuke", 1, 13, 7, False)])
    add_series("t0-02", 0, 2, "bo3", R2, [
        ("Overpass", 10, 13, 6, False), ("Ancient", 10, 8, 13, False), ("Dust2", 11, 7, 13, False)])
    # Temporada 1.
    add_series("t1-01", 1, 1, "bo3", R1, [
        ("Inferno", 1, 13, 8, True), ("Mirage", 1, 10, 13, False), ("Train", 2, 13, 11, False)])
    add_series("t1-02", 1, 2, "bo1", R2, [("Mirage", 5, 13, 6, True)])
    add_series("t1-03", 1, 3, "bo1", R3, [("Ancient", 8, 9, 13, False)], names=("PL", "PT"))
    add_series("t1-04", 1, 4, "bo3", R2, [
        ("Nuke", 13, 7, 13, False), ("Overpass", 13, 13, 10, False), ("Anubis", 14, 5, 13, False)])
    add_series("t1-05", 1, 5, "bo1", R1, [("Dust2", 17, 13, 10, True)])
    add_series("t1-06", 1, 6, "bo3", R3, [("Vertigo", 20, 13, 7, False)], status="pending")
    series.append({
        "id": "ser-t1-07", "season_number": 1, "sequence_number": 7, "match_format": "bo3",
        "status": "pending", "winner_side": None, "team_a_name": "PT", "team_b_name": "PL",
        "played_on": None,
    })

    # Mapas antigos sem confronto vinculado (rosters de oito jogadores).
    legacy = [
        ("legacy-1", "2026-09-20", "Inferno", 22, "Team 1 venceu por 13 a 9 sobre Team 2.", [0, 2, 4, 6], [1, 3, 5, 7]),
        ("legacy-2", "2026-09-27", "Mirage", 24, "Placar oficial: Team 1 11 – 13 Team 2", [1, 3, 5, 7], [0, 2, 4, 6]),
    ]
    for label, played, map_name, rounds, notes, win_team, lose_team in legacy:
        match_id = _mid(label)
        won_first = label == "legacy-1"
        matches.append({
            "id": match_id, "played_at": played, "map_name": map_name, "source": SOURCE_DEMO,
            "rounds_total": rounds, "notes": notes, "team_a_name": None, "team_b_name": None,
            "team_a_score": None, "team_b_score": None, "result_verified": False,
        })
        a_idx, b_idx = (win_team, lose_team) if won_first else (win_team, lose_team)
        lines, _ = _stats_for(rng, match_id, a_idx + b_idx, set(a_idx), 13, rounds - 13)
        stats.extend(lines)

    seasons = [
        {"number": 0, "label": "Temporada 0 (experimental)", "starts_on": "2026-10-01",
         "ends_on": "2026-10-18", "bo3_target": None, "homologated_at": "2026-10-19T09:00:00+00:00"},
        {"number": 1, "label": "Temporada 1", "starts_on": "2026-10-19", "ends_on": "2026-11-18",
         "bo3_target": None, "homologated_at": None},
        {"number": 2, "label": "Temporada 2", "starts_on": "2026-11-19", "ends_on": "2026-12-18",
         "bo3_target": None, "homologated_at": None},
    ]
    frozen = [{"season_number": s, "player_id": p["id"], "stars": p["stars"]}
              for s in (0, 1) for p in players]

    # Classificação final e títulos da Temporada 0, calculados pelo método legado.
    from edb.core import enrich, leaderboard
    t0_ids = {m["match_id"] for m in series_maps if m["series_id"].startswith("ser-t0")}
    t0_matches = [m for m in matches if m["id"] in t0_ids]
    t0_stats = [s for s in stats if s["match_id"] in t0_ids]
    board = leaderboard(enrich(players, t0_matches, t0_stats), min_games=2)
    final_rankings, titles = [], []
    sort_field = {"elite": "Elite", "superacao": "Superação %", "xp": "XP"}
    for rank_type, field in sort_field.items():
        ordered = board.sort_values(field, ascending=False).reset_index(drop=True)
        for order, row in enumerate(json.loads(ordered.to_json(orient="records")), 1):
            row["__order"] = order
            final_rankings.append({"season_number": 0, "rank_type": rank_type,
                                   "player_id": str(row["player_id"]), "rank_data": row})
        champion = ordered[ordered["Elegível"] == True].iloc[0]  # noqa: E712
        titles.append({"season_number": 0, "rank_type": rank_type,
                       "player_id": str(champion["player_id"]), "score": float(champion[field])})

    return {
        "players": players, "matches": matches, "player_stats": stats,
        "player_scope_stats": scope, "league_seasons": seasons, "bo3_series": series,
        "bo3_maps": series_maps, "bo3_players": series_players,
        "season_player_stars": frozen, "season_final_rankings": final_rankings,
        "season_titles": titles, "player_aliases": [],
    }


class DemoStore(Store):
    """Store em memória que imita o PostgREST/RPC do Supabase usado em produção."""

    def __init__(self, data: dict | None = None):
        self.url = "https://demo.invalid"
        self.key = "demo"
        self.cloud = True
        self.db_file = None
        self.data = data if data is not None else build_demo_data()
        self._mutex = RLock()

    # Leituras ------------------------------------------------------------------
    def _list(self, table):
        with self._mutex:
            return [dict(row) for row in self.data.get(table, [])]

    def players(self):
        return self._list("players")

    def matches(self):
        return self._list("matches")

    def stats(self):
        return self._list("player_stats")

    def scope_stats(self):
        return self._list("player_scope_stats")

    # API estilo PostgREST --------------------------------------------------------
    @staticmethod
    def _filters(params):
        return {k: v[3:] for k, v in (params or {}).items()
                if isinstance(v, str) and v.startswith("eq.")}

    def _api(self, method, table, *, params=None, payload=None):
        with self._mutex:
            if table.startswith("rpc/"):
                return self._rpc(table[4:], payload or {})
            rows = self.data.setdefault(table, [])
            filters = self._filters(params)

            def hit(row):
                return all(str(row.get(k)) == v for k, v in filters.items())

            if method == "GET":
                return [dict(r) for r in rows if hit(r)]
            if method == "POST":
                items = payload if isinstance(payload, list) else [payload]
                keys = (params or {}).get("on_conflict", "id").split(",")
                for item in items:
                    existing = next((r for r in rows if all(str(r.get(k)) == str(item.get(k)) for k in keys)), None)
                    if existing is not None:
                        existing.update(item)
                    else:
                        rows.append(dict(item))
                return items
            if method == "PATCH":
                changed = [r for r in rows if hit(r)]
                for row in changed:
                    row.update(payload or {})
                return [dict(r) for r in changed]
            if method == "DELETE":
                removed = [r for r in rows if hit(r)]
                self.data[table] = [r for r in rows if not hit(r)]
                if table == "matches":
                    ids = {r["id"] for r in removed}
                    self.data["player_stats"] = [s for s in self.data.get("player_stats", []) if s["match_id"] not in ids]
                return removed
        raise RuntimeError("Operação não suportada no modo demonstração.")

    def _rpc(self, name, payload):
        if name == "ensure_edb_calendar":
            return 1
        if name == "register_edb_confronto":
            return self._register_confront(payload["p_bundle"])
        if name == "homologate_edb_season":
            return self._homologate(payload)
        raise RuntimeError("RPC desconhecida no modo demonstração: " + name)

    def _register_confront(self, bundle):
        season = int(bundle["season_number"])
        existing = [s for s in self.data["bo3_series"] if int(s["season_number"]) == season]
        sequence = max([int(s["sequence_number"]) for s in existing], default=0) + 1
        sid = "ser-" + uuid.uuid4().hex[:12]
        wins = {"a": 0, "b": 0}
        team_a = set(bundle["team_a_player_ids"])
        stats = self.data["player_stats"]
        first_day = None
        for number, item in enumerate(bundle["matches"], 1):
            a, b = int(item["team_a_score"]), int(item["team_b_score"])
            side = "a" if a > b else "b"
            wins[side] += 1
            match = next(m for m in self.data["matches"] if m["id"] == item["match_id"])
            match.update({"team_a_name": bundle["team_a_name"], "team_b_name": bundle["team_b_name"],
                          "team_a_score": a, "team_b_score": b, "result_verified": True})
            first_day = first_day or str(match["played_at"])[:10]
            for stat in stats:
                if stat["match_id"] == item["match_id"]:
                    stat["won"] = (stat["player_id"] in team_a) == (a > b)
            self.data["bo3_maps"].append({"series_id": sid, "match_id": item["match_id"],
                                          "map_number": number, "winner_side": side})
        fmt = bundle["format"]
        need = 1 if fmt == "bo1" else 2
        winner = "a" if wins["a"] >= need else "b" if wins["b"] >= need else None
        self.data["bo3_series"].append({
            "id": sid, "season_number": season, "sequence_number": sequence, "match_format": fmt,
            "status": "completed", "winner_side": winner, "team_a_name": bundle["team_a_name"],
            "team_b_name": bundle["team_b_name"], "played_on": first_day,
        })
        roster = {s["player_id"] for item in bundle["matches"] for s in stats if s["match_id"] == item["match_id"]}
        for pid in roster:
            self.data["bo3_players"].append({"series_id": sid, "player_id": pid,
                                             "team_side": "a" if pid in team_a else "b"})
        return {"series_id": sid}

    def _homologate(self, payload):
        season = int(payload["p_season"])
        for row in self.data["league_seasons"]:
            if int(row["number"]) == season:
                row["homologated_at"] = "2026-11-19T09:00:00+00:00"
        for item in payload.get("p_rankings", []):
            self.data["season_final_rankings"].append({
                "season_number": season, "rank_type": item["rank_type"],
                "player_id": item["player_id"], "rank_data": item["rank_data"]})
        for item in payload.get("p_titles", []):
            self.data["season_titles"].append({
                "season_number": season, "rank_type": item["rank_type"],
                "player_id": item["player_id"], "score": item["score"]})
        return {"ok": True}
