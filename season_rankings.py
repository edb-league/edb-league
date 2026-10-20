"""Rankings mensais oficiais da EDB LEAGUE (Temporada 1 em diante).

Os seis melhores mapas sao selecionados independentemente por indicador.
A Temporada 0 usa o calculo legado e nao sofre recalculo retroativo.
"""
from __future__ import annotations

import pandas as pd
from season_system import season_dates

from core import TARGET_KPR, leaderboard

RANK_TYPES = ("elite", "superacao", "xp")
MAX_MAPS = 6
MIN_MAPS = 6
COLUMNS = [
    "player_id", "Jogador", "Estrelas", "Partidas", "Mapas disputados",
    "Kills", "K/D", "KPR", "ADR", "Vitórias", "Elite", "Superação %",
    "XP", "Elegível", "Mapas selecionados", "__score_precise",
    "__kpr_precise", "__adr_precise", "__wins_precise",
    "__elite_precise", "__order",
]


def _score_elite(kills, rounds, damage):
    kpr = float(kills) / max(float(rounds), 1.0)
    if pd.isna(damage):
        return 100.0 * kpr / 0.75
    adr = float(damage) / max(float(rounds), 1.0)
    return 100.0 * (0.6 * kpr / 0.75 + 0.4 * adr / 75.0)


def _xp_mensal(g, stars, season_number):
    """Uma missão por semana de sete dias desde o dia 19 (4 ou 5 semanas/mês).

    Só os seis mapas escolhidos no ranking de XP entram no cálculo.
    """
    xp = 40 * len(g) + 20 * int((g["won"] == True).sum())
    if g.empty:
        return int(xp)
    start, end = season_dates(season_number)
    chosen = g.copy()
    chosen["kpr"] = chosen["kills"] / chosen["rounds"]
    days = (pd.to_datetime(chosen["played_at"]) - pd.Timestamp(start)).dt.days
    length = (end - start).days + 1
    chosen["season_week"] = (days // 7).clip(lower=0, upper=(length-1)//7)
    for _, weekly in chosen.groupby("season_week"):
        if ((weekly["kpr"] >= TARGET_KPR[int(stars)])
                & (weekly["rounds"] >= 8)).any():
            xp += 100
    return int(xp)


def _aggregate(g, stars, season_number):
    kills = int(g["kills"].sum())
    deaths = int(g["deaths"].sum())
    rounds = max(float(g["rounds"].sum()), 1.0)
    kpr = kills / rounds
    has_damage = g["damage"].notna().all()
    damage = float(g["damage"].sum()) if has_damage else float("nan")
    adr = damage / rounds if has_damage else float("nan")
    elite = _score_elite(kills, rounds, damage)
    supera = 100.0 * (kpr / TARGET_KPR[int(stars)] - 1)
    wins = int((g["won"] == True).sum())
    return {
        "Kills": kills, "K/D": round(kills / max(deaths, 1), 2),
        "KPR": round(kpr, 3), "ADR": round(adr, 1) if pd.notna(adr) else None,
        "Vitórias": wins, "Elite": round(elite, 1),
        "Superação %": round(supera, 1),
        "XP": _xp_mensal(g, stars, season_number),
        "_kpr": kpr, "_adr": adr if pd.notna(adr) else -1.0,
        "_elite": elite, "_supera": supera,
    }


def _best(g, rank_type, stars):
    t = g.copy()
    t["__map_kpr"] = t["kills"] / t["rounds"]
    if rank_type == "elite":
        t["__pick_score"] = t.apply(
            lambda row: _score_elite(row["kills"], row["rounds"], row["damage"]),
            axis=1,
        )
    elif rank_type == "superacao":
        t["__pick_score"] = 100.0 * (
            t["__map_kpr"] / TARGET_KPR[int(stars)] - 1
        )
    else:
        # O XP por mapa tem peso de 40 + 20 por vitoria;
        # missao semanal so pode ser concluida nos seis mapas escolhidos.
        t["__pick_score"] = 40 + 20 * (t["won"] == True).astype(int)
    return t.sort_values(
        ["__pick_score", "played_at", "match_id"],
        ascending=[False, True, True], kind="mergesort",
    ).head(MAX_MAPS).copy()


def season_boards(frame, season_number, frozen_stars=None):
    """Retorna boards para Elite, Superacao e XP, com elegibilidade em seis mapas.

    A Temporada 0 preserva o mecanismo antigo de quatro mapas por semana,
    enquanto a partir da 1 cada ranking escolhe seus seis melhores mapas.
    """
    t = frame.copy()
    frozen_stars = frozen_stars or {}
    if not t.empty:
        t["stars"] = [
            int(frozen_stars.get(str(pid), stars))
            for pid, stars in zip(t["player_id"], t["stars"])
        ]
    if int(season_number) == 0:
        old_board = leaderboard(t, min_games=2)
        return {key: old_board.copy() for key in RANK_TYPES}
    if t.empty:
        return {key: pd.DataFrame(columns=COLUMNS) for key in RANK_TYPES}
    for name in ["kills", "deaths", "assists", "rounds", "damage"]:
        t[name] = pd.to_numeric(t[name], errors="coerce")
    t = t.dropna(subset=["rounds"])
    t = t[t["rounds"] > 0].drop_duplicates(["player_id", "match_id"])
    if t.empty:
        return {key: pd.DataFrame(columns=COLUMNS) for key in RANK_TYPES}
    outputs = {key: [] for key in RANK_TYPES}
    for player_id, g in t.groupby("player_id", sort=False):
        g = g.sort_values(["played_at", "match_id"]).copy()
        first = g.iloc[0]
        stars = max(1, min(5, int(first["stars"])))
        eligible = len(g) >= MIN_MAPS
        groups = {key: _best(g, key, stars) for key in RANK_TYPES}
        values = {key: _aggregate(sub, stars, season_number) for key, sub in groups.items()}
        for key in RANK_TYPES:
            current = values[key]
            row = {
                "player_id": str(player_id),
                "Jogador": str(first["nickname"]),
                "Estrelas": stars,
                "Partidas": len(groups[key]),
                "Mapas disputados": len(g),
                "Kills": current["Kills"],
                "K/D": current["K/D"],
                "KPR": current["KPR"],
                "ADR": current["ADR"],
                "Vitórias": current["Vitórias"],
                # Cada indicador tem seu proprio conjunto dos seis melhores mapas.
                "Elite": values["elite"]["Elite"],
                "Superação %": values["superacao"]["Superação %"],
                "XP": values["xp"]["XP"],
                "Elegível": bool(eligible),
                "Mapas selecionados": list(groups[key]["match_id"].astype(str)),
                "__score_precise": (
                    values["elite"]["_elite"] if key == "elite" else
                    values["superacao"]["_supera"] if key == "superacao" else
                    float(values["xp"]["XP"])
                ),
                "__kpr_precise": current["_kpr"],
                "__adr_precise": current["_adr"],
                "__wins_precise": current["Vitórias"],
                "__elite_precise": values["elite"]["_elite"],
            }
            outputs[key].append(row)
    boards = {}
    for key, rows in outputs.items():
        df = pd.DataFrame(rows)
        if key == "xp":
            tie_fields = ["__wins_precise", "__elite_precise"]
        else:
            tie_fields = ["__kpr_precise", "__adr_precise"]
        df = df.sort_values(
            ["Elegível", "__score_precise", *tie_fields, "Jogador"],
            ascending=[False, False, False, False, True],
            kind="mergesort",
        ).reset_index(drop=True)
        df["__order"] = range(1, len(df) + 1)
        boards[key] = df
    return boards


def has_technical_tie(df, rank_type):
    """Empate integral do campeao nos criterios do regulamento."""
    if df is None or len(df) < 2:
        return False
    qualified = df[df["Elegível"] == True]
    if len(qualified) < 2:
        return False
    a, b = qualified.iloc[0], qualified.iloc[1]
    if rank_type == "xp":
        fields = ("__score_precise", "__wins_precise", "__elite_precise")
    else:
        fields = ("__score_precise", "__kpr_precise", "__adr_precise")
    return all(a[k] == b[k] for k in fields)
