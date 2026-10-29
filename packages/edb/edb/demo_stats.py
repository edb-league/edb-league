"""Estatísticas completas de uma demo CS2, no estilo do perfil de jogador da HLTV.

As regras foram calibradas contra o SCOPE.GG em três partidas do servidor XPLAY.GG
(kills, mortes, assistências, dano, KAST, aberturas, trades, utilitários).

Regras que importam:
- A partida começa no ÚLTIMO ``begin_new_match``. O round faca e o warmup ficam de fora.
- Dano efetivo: ``min(dmg_health, vida restante da vítima)`` por (round, vítima).
- Assistência não inclui flash assist, que é contada à parte.
- Trade: o autor da morte é morto por um companheiro da vítima em até 5 s (320 ticks).
- KAST: truncado, não arredondado.
- Abertura: primeira kill válida do round (sem fogo amigo).

Requer ``demoparser2`` (extra ``demo`` do pacote).
"""
from __future__ import annotations

from bisect import bisect_right
from collections import Counter, defaultdict

import pandas as pd

PARSER_VERSION = 2  # 2: ordenação estável por tick
TRADE_TICKS = 320
TICKRATE = 64

SNIPERS = {"awp", "ssg08", "scar20", "g3sg1"}
RIFLES = {"ak47", "m4a1", "m4a1_silencer", "galilar", "famas", "aug", "sg556"}
SMGS = {"mac10", "mp9", "mp7", "mp5sd", "ump45", "p90", "bizon"}
PISTOLS = {"glock", "hkp2000", "usp_silencer", "p250", "fiveseven", "tec9", "cz75a", "deagle", "elite", "revolver"}
GRENADES = {"hegrenade", "inferno", "molotov", "incgrenade"}
THROWN = {
    "flashbang": "flashes_thrown",
    "hegrenade": "he_thrown",
    "molotov": "molotovs_thrown",
    "incgrenade": "molotovs_thrown",
    "smokegrenade": "smokes_thrown",
}
EVENTS = [
    "player_death", "player_hurt", "player_blind", "round_start", "round_freeze_end", "round_end",
    "begin_new_match", "bomb_planted", "bomb_defused", "weapon_fire", "smokegrenade_detonate",
]
# Contagens por jogador gravadas na tabela player_match_detail (além de weapon_kills e clutches).
COUNT_FIELDS = [
    "rounds_t", "rounds_ct", "rounds_won", "rounds_won_t", "rounds_won_ct",
    "kills_t", "kills_ct", "deaths_t", "deaths_ct", "assists_t", "assists_ct",
    "damage_t", "damage_ct", "damage_taken", "kast_rounds_t", "kast_rounds_ct",
    "kills_in_won_rounds", "damage_in_won_rounds",
    "rk1_t", "rk2_t", "rk3_t", "rk4_t", "rk5_t", "rk1_ct", "rk2_ct", "rk3_ct", "rk4_ct", "rk5_ct",
    "opening_kills_t", "opening_kills_ct", "opening_deaths_t", "opening_deaths_ct",
    "opening_kill_rounds_won", "opening_kills_in_won_rounds",
    "trade_kills", "deaths_traded", "assisted_kills", "flash_assists",
    "headshots", "sniper_kills", "awp_kills", "rifle_kills", "smg_kills", "pistol_kills", "grenade_kills", "other_kills",
    "smoke_kills", "wallbang_kills", "noscope_kills", "blind_kills",
    "rounds_with_sniper", "rounds_with_awp",
    "time_alive_seconds", "rounds_with_plant_t", "rounds_with_plant_ct", "alive_post_plant_t", "alive_post_plant_ct",
    "last_alive_rounds", "clutches_won",
    "flashes_thrown", "he_thrown", "molotovs_thrown", "smokes_thrown", "smokes_detonated",
    "he_damage", "fire_damage", "enemies_flashed", "flash_seconds", "plants", "defuses",
]


def _weapon_class(weapon: str) -> str:
    if weapon in SNIPERS:
        return "sniper"
    if weapon in RIFLES:
        return "rifle"
    if weapon in SMGS:
        return "smg"
    if weapon in PISTOLS:
        return "pistol"
    if weapon in GRENADES:
        return "grenade"
    return "other"


def _empty() -> pd.DataFrame:
    return pd.DataFrame(columns=["tick"])


def _is_id(value) -> bool:
    return str(value).isdigit()


def analyze(path: str, trade_ticks: int = TRADE_TICKS, tickrate: int = TICKRATE) -> dict:
    """Lê a demo e devolve o resumo da partida e as contagens de cada jogador."""
    from demoparser2 import DemoParser

    parser = DemoParser(path)
    header = parser.parse_header()
    raw = dict(parser.parse_events(EVENTS, player=["team_num"], other=["total_rounds_played", "is_warmup_period"]))
    ev = {name: raw.get(name, _empty()) for name in EVENTS}

    begins = ev["begin_new_match"]
    start = int(begins.tick.max()) if len(begins) else 0

    def live(df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            return _empty()
        mask = df.tick > start
        if "is_warmup_period" in df:
            mask &= ~df.is_warmup_period.fillna(False).astype(bool)
        return df[mask].sort_values("tick", kind="stable").copy()

    starts_df = ev["round_start"]
    round_starts = sorted(starts_df[starts_df.tick >= start - 5].tick.tolist()) if len(starts_df) else []
    ends = live(ev["round_end"])
    n_rounds = len(ends)
    if n_rounds == 0 or not round_starts:
        raise ValueError("Demo sem rounds válidos depois do início da partida.")
    freeze = sorted(ev["round_freeze_end"].tick.tolist()) if len(ev["round_freeze_end"]) else []

    def round_of(tick: int) -> int:
        return min(max(bisect_right(round_starts, tick), 1), n_rounds)

    deaths, hurts, blinds = live(ev["player_death"]), live(ev["player_hurt"]), live(ev["player_blind"])
    fires = ev["weapon_fire"]
    fires = fires[fires.tick > start].sort_values("tick", kind="stable").copy() if len(fires) else _empty()
    for frame in (deaths, hurts):
        frame["rnd"] = frame.tick.apply(round_of)
    for column in ("attacker_steamid", "user_steamid", "assister_steamid"):
        if column in deaths:
            deaths[column] = deaths[column].astype(str)
    hurts["att"] = hurts.attacker_steamid.astype(str)
    hurts["vic"] = hurts.user_steamid.astype(str)

    # Dano efetivo: limitado à vida que a vítima tinha antes do golpe.
    life, effective = {}, []
    for row in hurts.itertuples():
        key = (row.rnd, row.vic)
        effective.append(min(row.dmg_health, life.get(key, 100)))
        life[key] = row.health
    hurts["eff"] = effective
    enemy_hits = hurts[(hurts.attacker_team_num != hurts.user_team_num) & hurts.att.str.isdigit()]

    # Times: o rótulo é o lado que o time tinha no round 1 (2 = T, 3 = CT).
    team_r1: dict[str, int] = {}
    try:
        snap = parser.parse_ticks(["team_num", "name"], ticks=[round_starts[0] + 200])
        for row in snap.itertuples():
            if _is_id(row.steamid) and int(row.team_num) in (2, 3):
                team_r1[str(row.steamid)] = int(row.team_num)
    except Exception:  # noqa: BLE001 - o parser lança erros de vários tipos
        pass
    for row in deaths.itertuples():  # substitutos que entraram depois
        for sid, team in ((row.attacker_steamid, row.attacker_team_num), (row.user_steamid, row.user_team_num)):
            if _is_id(sid) and sid not in team_r1 and int(team) in (2, 3):
                team_r1[sid] = int(team) if row.rnd <= 12 else 5 - int(team)
    nicks: dict[str, str] = {}
    for row in deaths.itertuples():
        for sid, name in ((row.attacker_steamid, row.attacker_name), (row.user_steamid, row.user_name)):
            if _is_id(sid):
                nicks[sid] = name
    teams = {2: [s for s, t in team_r1.items() if t == 2], 3: [s for s, t in team_r1.items() if t == 3]}

    # Lado de cada time em cada round. Regra padrão (troca após o round 12), corrigida pelo que a demo mostra.
    side_of: dict[int, dict[int, int]] = {}
    seen: dict[int, dict[int, int]] = defaultdict(dict)
    for frame, pairs in (
        (deaths, (("attacker_steamid", "attacker_team_num"), ("user_steamid", "user_team_num"))),
        (hurts, (("att", "attacker_team_num"), ("vic", "user_team_num"))),
    ):
        for row in frame.itertuples():
            for id_col, team_col in pairs:
                sid, side = getattr(row, id_col), getattr(row, team_col)
                if sid in team_r1 and int(side) in (2, 3):
                    seen[row.rnd].setdefault(team_r1[sid], int(side))
    for rno in range(1, n_rounds + 1):
        mapping = {}
        for label in (2, 3):
            if label in seen[rno]:
                mapping[label] = seen[rno][label]
            elif 5 - label in seen[rno]:
                mapping[label] = 5 - seen[rno][5 - label]
            elif rno - 1 in side_of and rno > 24:
                mapping[label] = side_of[rno - 1][label]
            else:
                mapping[label] = label if rno <= 12 else 5 - label
        side_of[rno] = mapping

    won_label: dict[int, int] = {}
    ends_tick: dict[int, int] = {}
    score = {2: 0, 3: 0}
    for rno, row in enumerate(ends.itertuples(), start=1):
        side = 2 if row.winner == "T" else 3
        label = next(lab for lab, s in side_of[rno].items() if s == side)
        won_label[rno] = label
        ends_tick[rno] = int(row.tick)
        score[label] += 1

    def freeze_tick(rno: int) -> int:
        later = [t for t in freeze if t >= round_starts[rno - 1]]
        return later[0] if later else round_starts[rno - 1] + 15 * tickrate

    plants = live(ev["bomb_planted"])
    plant_tick = {}
    for row in plants.itertuples():
        plant_tick.setdefault(round_of(row.tick), int(row.tick))

    stats: dict[str, dict] = defaultdict(lambda: {name: 0 for name in COUNT_FIELDS})
    weapons: dict[str, Counter] = defaultdict(Counter)
    clutches: dict[str, dict] = defaultdict(lambda: {f"1v{n}": [0, 0] for n in range(1, 6)})

    def sfx(sid: str, rno: int) -> str:
        return "t" if side_of[rno][team_r1[sid]] == 2 else "ct"

    # Dano causado e recebido, por lado.
    for row in enemy_hits.itertuples():
        if row.att in team_r1:
            stats[row.att]["damage_" + sfx(row.att, row.rnd)] += int(row.eff)
            if team_r1[row.att] == won_label[row.rnd]:
                stats[row.att]["damage_in_won_rounds"] += int(row.eff)
            if row.weapon == "hegrenade":
                stats[row.att]["he_damage"] += int(row.eff)
            elif row.weapon in GRENADES:
                stats[row.att]["fire_damage"] += int(row.eff)
        if row.vic in team_r1:
            stats[row.vic]["damage_taken"] += int(row.eff)

    sniper_rounds: dict[int, set] = defaultdict(set)
    awp_rounds: dict[int, set] = defaultdict(set)
    for row in fires.itertuples():
        sid = str(row.user_steamid)
        if sid not in team_r1:
            continue
        weapon = str(row.weapon).removeprefix("weapon_")
        rno = round_of(row.tick)
        if weapon in THROWN:
            stats[sid][THROWN[weapon]] += 1
        if weapon in SNIPERS:
            sniper_rounds[rno].add(sid)
        if weapon == "awp":
            awp_rounds[rno].add(sid)

    deaths_by_round = {rno: g.to_dict("records") for rno, g in deaths.groupby("rnd")}
    for rno in range(1, n_rounds + 1):
        events = deaths_by_round.get(rno, [])
        alive = {2: set(teams[2]), 3: set(teams[3])}
        first_done, kills_round = False, Counter()
        assisted, died, traded, death_tick, clutch_done = set(), set(), set(), {}, set()
        won = won_label[rno]
        for sid in team_r1:
            st = stats[sid]
            st["rounds_" + sfx(sid, rno)] += 1
            if team_r1[sid] == won:
                st["rounds_won"] += 1
                st["rounds_won_" + sfx(sid, rno)] += 1
        for e in events:
            a, v, x = e["attacker_steamid"], e["user_steamid"], e["assister_steamid"]
            friendly = e["attacker_team_num"] == e["user_team_num"]
            valid = _is_id(a) and a != v and not friendly and a in team_r1
            if v in team_r1:
                stats[v]["deaths_" + sfx(v, rno)] += 1
                died.add(v)
                death_tick[v] = int(e["tick"])
                alive[team_r1[v]].discard(v)
            if valid:
                st, weapon = stats[a], str(e["weapon"])
                side = sfx(a, rno)
                st["kills_" + side] += 1
                kills_round[a] += 1
                kind = _weapon_class(weapon)
                st[kind + "_kills"] += 1
                if weapon == "awp":
                    st["awp_kills"] += 1
                weapons[a][weapon] += 1
                if str(e["headshot"]).lower() == "true":
                    st["headshots"] += 1
                if e["thrusmoke"]:
                    st["smoke_kills"] += 1
                if e["noscope"]:
                    st["noscope_kills"] += 1
                if e["penetrated"]:
                    st["wallbang_kills"] += 1
                if e["attackerblind"]:
                    st["blind_kills"] += 1
                if team_r1[a] == won:
                    st["kills_in_won_rounds"] += 1
                if _is_id(x) and x not in (a, v):
                    st["assisted_kills"] += 1
                if not first_done:
                    first_done = True
                    st["opening_kills_" + side] += 1
                    if team_r1[a] == won:
                        st["opening_kills_in_won_rounds"] += 1
                        st["opening_kill_rounds_won"] += 1
                    if v in team_r1:
                        stats[v]["opening_deaths_" + sfx(v, rno)] += 1
            if _is_id(x) and x not in (a, v) and not friendly and x in team_r1:
                if str(e["assistedflash"]).lower() == "true":
                    stats[x]["flash_assists"] += 1
                else:
                    stats[x]["assists_" + sfx(x, rno)] += 1
                assisted.add(x)
            if v in team_r1:
                team = team_r1[v]
                if len(alive[team]) == 1 and len(alive[5 - team]) >= 1:
                    last = next(iter(alive[team]))
                    if last not in clutch_done:
                        clutch_done.add(last)
                        stats[last]["last_alive_rounds"] += 1
                        size = min(len(alive[5 - team]), 5)
                        clutches[last][f"1v{size}"][0] += 1
                        if won == team:
                            clutches[last][f"1v{size}"][1] += 1
                            stats[last]["clutches_won"] += 1
        for i, e in enumerate(events):  # trades
            a, v = e["attacker_steamid"], e["user_steamid"]
            if e["attacker_team_num"] == e["user_team_num"] or not _is_id(a):
                continue
            for f in events[i + 1:]:
                if f["tick"] - e["tick"] > trade_ticks:
                    break
                if f["user_steamid"] == a and f["attacker_team_num"] == e["user_team_num"] and _is_id(f["attacker_steamid"]):
                    if f["attacker_steamid"] in team_r1:
                        stats[f["attacker_steamid"]]["trade_kills"] += 1
                    traded.add(v)
                    if v in team_r1:
                        stats[v]["deaths_traded"] += 1
                    break
        fe, end = freeze_tick(rno), ends_tick[rno]
        for sid in team_r1:
            st, side = stats[sid], sfx(sid, rno)
            if sid in kills_round or sid in assisted or sid not in died or sid in traded:
                st["kast_rounds_" + side] += 1
            k = min(kills_round.get(sid, 0), 5)
            if k:
                st[f"rk{k}_{side}"] += 1
            st["time_alive_seconds"] += max((death_tick.get(sid, end) - fe) / tickrate, 0)
            if sid in sniper_rounds[rno]:
                st["rounds_with_sniper"] += 1
            if sid in awp_rounds[rno]:
                st["rounds_with_awp"] += 1
            if rno in plant_tick:
                st["rounds_with_plant_" + side] += 1
                if sid not in died or death_tick[sid] > plant_tick[rno]:
                    st["alive_post_plant_" + side] += 1

    for row in blinds[(blinds.attacker_team_num != blinds.user_team_num) & blinds.attacker_steamid.astype(str).str.isdigit()].itertuples():
        sid = str(row.attacker_steamid)
        if sid in team_r1:
            stats[sid]["enemies_flashed"] += 1
            stats[sid]["flash_seconds"] += float(row.blind_duration)
    for key, frame in (("plants", plants), ("defuses", live(ev["bomb_defused"]))):
        for row in frame.itertuples():
            if str(row.user_steamid) in team_r1:
                stats[str(row.user_steamid)][key] += 1
    smokes = live(ev["smokegrenade_detonate"])
    for row in smokes.itertuples():
        if str(row.user_steamid) in team_r1:
            stats[str(row.user_steamid)]["smokes_detonated"] += 1

    players = []
    for sid in sorted(team_r1, key=lambda s: -(stats[s]["kills_t"] + stats[s]["kills_ct"])):
        row = dict(stats[sid])
        row["time_alive_seconds"] = round(row["time_alive_seconds"], 1)
        row["flash_seconds"] = round(row["flash_seconds"], 2)
        row.update(
            steamid=sid, nick=nicks.get(sid, sid), team=team_r1[sid], rounds=n_rounds,
            kills=row["kills_t"] + row["kills_ct"], deaths=row["deaths_t"] + row["deaths_ct"],
            assists=row["assists_t"] + row["assists_ct"], damage=row["damage_t"] + row["damage_ct"],
            kast_rounds=row["kast_rounds_t"] + row["kast_rounds_ct"],
            open_kills=row["opening_kills_t"] + row["opening_kills_ct"],
            weapon_kills=dict(weapons[sid]), clutches=clutches[sid] if sid in clutches else {f"1v{n}": [0, 0] for n in range(1, 6)},
        )
        row["kast"] = int(100 * row["kast_rounds"] / n_rounds)
        players.append(row)
    return {
        "parser_version": PARSER_VERSION,
        "map": str(header.get("map_name", "")).removeprefix("de_"),
        "server": header.get("server_name"),
        "rounds": n_rounds,
        "overtime": n_rounds > 24,
        "score": {"team_t_first": score[2], "team_ct_first": score[3]},
        "rosters": {"team_t_first": teams[2], "team_ct_first": teams[3]},
        "players": players,
    }
