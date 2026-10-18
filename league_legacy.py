"""EDB LEAGUE: estatísticas históricas por identidade estável, sem limitar partidas."""
from __future__ import annotations
from datetime import datetime
import pandas as pd


def _number(raw):
    try:
        if raw is None or pd.isna(raw):
            return None
        return float(raw)
    except (ValueError, TypeError):
        return None


def _int(raw):
    x = _number(raw)
    return int(x) if x is not None else 0


def _date(raw):
    stamp = pd.to_datetime(raw, errors="coerce")
    return None if pd.isna(stamp) else stamp


def _player_name(player):
    nick = str(player.get("nickname") or "Jogador")
    real = str(player.get("real_name") or "").strip()
    return f"{real} ({nick})" if real and real.casefold() != nick.casefold() else nick


def match_records(players, matches, stats, scope):
    """Retorna uma linha válida por jogador/partida, preservando o nick histórico."""
    by_player = {str(p["id"]): p for p in players}
    by_match = {str(m["id"]): m for m in matches}
    extras = {(str(x["match_id"]), str(x["player_id"])): x for x in scope}
    records = []
    seen = set()
    for stat in stats:
        pid, mid = str(stat.get("player_id")), str(stat.get("match_id"))
        if (mid, pid) in seen or pid not in by_player or mid not in by_match:
            continue
        played = _date(by_match[mid].get("played_at"))
        if played is None:
            continue
        seen.add((mid, pid))
        p, m = by_player[pid], by_match[mid]
        add = extras.get((mid, pid), {})
        rounds = _int(stat.get("rounds"))
        damage = _number(stat.get("damage"))
        adr_source = _number(add.get("adr_reported"))
        adr_est = damage / rounds if damage is not None and rounds > 0 else None
        won = stat.get("won")
        if won in (True, 1, "1", "true"):
            won = True
        elif won in (False, 0, "0", "false"):
            won = False
        else:
            won = None
        kills, deaths = _int(stat.get("kills")), _int(stat.get("deaths"))
        observed = stat.get("observed_nickname")
        records.append({
            "player_id": pid, "match_id": mid,
            "player_name": _player_name(p), "nickname": p.get("nickname") or "",
            "played_nick": observed if observed and str(observed).strip() else p.get("nickname") or "",
            "date": played, "map": m.get("map_name") or "Mapa não informado",
            "kills": kills, "deaths": deaths, "assists": _int(stat.get("assists")),
            "damage": damage, "rounds": rounds, "won": won,
            "kpr": kills / rounds if rounds > 0 else None,
            "kd": kills / deaths if deaths > 0 else None,
            "adr": adr_source if adr_source is not None else adr_est,
            "adr_reported": adr_source,
            "grenade_damage": _number(add.get("grenade_damage")),
            "rating": _number(stat.get("rating")),
            "kast": _number(stat.get("kast")),
        })
    return sorted(records, key=lambda r: (r["date"], r["match_id"], r["player_id"]))


def player_summary(player_id, records):
    """Totais reais; jogos não são truncados pelo teto de XP semanal."""
    played = [r for r in records if r["player_id"] == str(player_id)]
    games = len(played)
    kills = sum(r["kills"] for r in played)
    deaths = sum(r["deaths"] for r in played)
    assists = sum(r["assists"] for r in played)
    rounds = sum(r["rounds"] for r in played)
    wins = sum(r["won"] is True for r in played)
    damage_rows = [r for r in played if r["damage"] is not None and r["rounds"] > 0]
    adr = (sum(r["damage"] for r in damage_rows) / sum(r["rounds"] for r in damage_rows)
           if damage_rows and len(damage_rows) == games and sum(r["rounds"] for r in damage_rows) else None)
    best = sorted(played, key=lambda r: (r["kills"], r["damage"] or 0), reverse=True)
    return {
        "games": games, "wins": wins, "win_rate": 100 * wins / games if games else None,
        "kills": kills, "deaths": deaths, "assists": assists,
        "kd": kills / deaths if deaths else None,
        "kpr": kills / rounds if rounds else None, "adr": adr,
        "best": best[0] if best else None, "matches": played,
    }


def hall_of_fame(records, min_games=2):
    """Recordes absolutos e acumulados; empates permanecem explícitos."""
    if not records:
        return []
    player_games = {}
    for r in records:
        player_games.setdefault(r["player_id"], []).append(r)

    def singles(title, metric, fmt, qualifier=lambda r: True):
        available = [r for r in records if r.get(metric) is not None and qualifier(r)]
        if not available:
            return None
        value = max(r[metric] for r in available)
        leaders = [r for r in available if r[metric] == value]
        return {
            "title": title, "value": fmt(value),
            "holders": [{"id": r["player_id"], "name": r["player_name"]} for r in leaders],
            "detail": " · ".join(dict.fromkeys(
                f"{r['map']} · {r['date'].strftime('%d/%m/%Y')}" for r in leaders
            )),
        }

    def totals(title, metric, fmt, condition=lambda rows: True):
        values = []
        for pid, rows in player_games.items():
            if condition(rows):
                value = metric(rows)
                values.append((pid, rows[0]["player_name"], value))
        if not values:
            return None
        high = max(x[2] for x in values)
        return {
            "title": title, "value": fmt(high),
            "holders": [{"id": p, "name": n} for p, n, value in values if value == high],
            "detail": f"Acumulado em todas as partidas registradas" if title != "Melhor K/D geral" else f"Mínimo de {min_games} partidas",
        }

    cards = [
        singles("Mais kills em uma partida", "kills", lambda n: f"{int(n)} kills"),
        singles("Maior ADR em uma partida", "adr", lambda n: f"{n:.1f} ADR",
                lambda r: r["rounds"] >= 8),
        singles("Melhor K/D em uma partida", "kd", lambda n: f"{n:.2f} K/D",
                lambda r: r["rounds"] >= 8),
        singles("Mais assistências em uma partida", "assists", lambda n: f"{int(n)} assistências"),
        singles("Mais dano de granadas", "grenade_damage", lambda n: f"{int(n)} de dano",
                lambda r: r["grenade_damage"] > 0),
        totals("Mais kills na liga", lambda rows: sum(x["kills"] for x in rows),
               lambda n: f"{int(n)} kills"),
        totals("Mais vitórias", lambda rows: sum(x["won"] is True for x in rows),
               lambda n: f"{int(n)} vitórias"),
        totals("Melhor K/D geral",
               lambda rows: (sum(x["kills"] for x in rows) /
                             max(1, sum(x["deaths"] for x in rows))),
               lambda n: f"{n:.2f} K/D",
               condition=lambda rows: len(rows) >= min_games and sum(x["deaths"] for x in rows) > 0),
    ]
    return [c for c in cards if c is not None]
