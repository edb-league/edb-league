"""Perfil de estatísticas no formato da página de jogador da HLTV.

Entrada: linhas de ``player_match_detail`` (contagens vindas da demo).
Saída: números prontos para a tela. Nada aqui acessa banco ou rede.

O que é igual à HLTV: Rating 1.0 (fórmula pública), KPR, DPR, ADR, KAST, multi-kill,
aberturas, clutches, armas e proporções de sniper.
O que é adaptado: Rating 2.0 (fórmula pública de 2017, usada como estimativa), as notas
0 a 100 (posição relativa na liga, não na cena profissional) e métricas cuja definição a
HLTV não publica (marcadas com ``adapted``). Rating 3.0 e Round Swing não são públicos
e não são calculados.
"""
from __future__ import annotations

from collections import defaultdict

SECTION_ORDER = ["firepower", "entrying", "trading", "opening", "closing", "sniping", "utility"]
SECTION_LABELS = {
    "firepower": ("Firepower", "poder de fogo"), "entrying": ("Entrying", "entrada"), "trading": ("Trading", "trocas"),
    "opening": ("Opening", "abertura"), "closing": ("Closing", "fechamento"), "sniping": ("Sniping", "sniper"),
    "utility": ("Utility", "utilitários"),
}
METRIC_NAMES = {
    "kpr": ("Kills per round", "kills por round"),
    "adr": ("Damage per round", "dano por round (ADR)"),
    "kprw": ("Kills per round win", "kills por round vencido"),
    "adr_won": ("Damage per round win", "dano por round vencido"),
    "rounds_with_kill": ("Rounds with a kill", "rounds com pelo menos 1 kill"),
    "rounds_multikill": ("Rounds with a multi-kill", "rounds com 2 ou mais kills"),
    "net_kills": ("Kill difference per 24 rounds", "saldo de kills a cada 24 rounds"),
    "net_damage": ("Damage difference per round", "saldo de dano por round"),
    "headshots": ("Headshot %", "porcentagem de kills com headshot"),
    "dpr": ("Deaths per round", "mortes por round"),
    "deaths_traded": ("Traded deaths", "mortes vingadas por um companheiro"),
    "apr": ("Assists per round", "assistências por round"),
    "opening_deaths_pr": ("Opening deaths per round", "mortes de abertura por round"),
    "trade_kills_pr": ("Trade kills per round", "kills de troca por round"),
    "trade_kills_pct": ("Trade kills", "kills de troca, em % das kills"),
    "assisted_kills": ("Assisted kills", "kills com assistência, em % das kills"),
    "opening_attempts": ("Opening attempts", "participação em aberturas"),
    "opening_kills": ("Opening kills", "kills de abertura"),
    "opening_deaths": ("Opening deaths", "mortes de abertura"),
    "opening_ratio": ("Opening kill ratio", "kills de abertura por morte de abertura"),
    "opening_success": ("Opening success", "aberturas vencidas, em %"),
    "win_after_opening": ("Win% after opening kill", "vitória do round após kill de abertura"),
    "first_kill_won": ("Opening kills in won rounds", "abertura em rounds vencidos"),
    "time_alive": ("Time alive per round", "tempo vivo por round"),
    "post_plant": ("Alive after plant", "vivo depois da bomba plantada"),
    "last_alive": ("Last alive", "rounds em que foi o último vivo"),
    "clutches_24": ("Clutches won per 24 rounds", "clutches vencidos a cada 24 rounds"),
    "clutch_win": ("Clutch win %", "aproveitamento em clutches"),
    "rounds_sniper": ("Rounds with sniper kills", "rounds com kill de sniper"),
    "sniper_kills": ("Sniper kills", "kills de sniper, em % das kills"),
    "rounds_awp": ("Rounds with AWP kills", "rounds com kill de AWP"),
    "awp_kills": ("AWP kills", "kills de AWP, em % das kills"),
    "util_damage": ("Utility damage per round", "dano de utilitário por round"),
    "he_damage": ("Grenade damage per round", "dano de granada HE por round"),
    "fire_damage": ("Molotov damage per round", "dano de molotov por round"),
    "flashes": ("Flashes thrown per round", "flashes lançadas por round"),
    "flash_assists": ("Flash assists per round", "assistências de flash por round"),
    "flashed": ("Enemies flashed per round", "inimigos cegados por round"),
    "flash_time": ("Blind time per round", "tempo de inimigo cego por round"),
    "smokes": ("Smokes thrown per round", "smokes lançadas por round"),
}
SUM_FIELDS = [
    "rounds_t", "rounds_ct", "rounds_won", "rounds_won_t", "rounds_won_ct", "kills_t", "kills_ct", "deaths_t",
    "deaths_ct", "assists_t", "assists_ct", "damage_t", "damage_ct", "damage_taken", "kast_rounds_t",
    "kast_rounds_ct", "kills_in_won_rounds", "damage_in_won_rounds",
    *[f"rk{n}_{s}" for n in range(1, 6) for s in ("t", "ct")],
    "opening_kills_t", "opening_kills_ct", "opening_deaths_t", "opening_deaths_ct", "opening_kill_rounds_won",
    "opening_kills_in_won_rounds", "trade_kills", "deaths_traded", "assisted_kills", "flash_assists",
    "headshots", "sniper_kills", "awp_kills", "rifle_kills", "smg_kills", "pistol_kills", "grenade_kills",
    "other_kills", "smoke_kills", "wallbang_kills", "noscope_kills", "blind_kills", "rounds_with_sniper",
    "rounds_with_awp", "time_alive_seconds", "rounds_with_plant_t", "rounds_with_plant_ct",
    "alive_post_plant_t", "alive_post_plant_ct", "last_alive_rounds", "clutches_won", "flashes_thrown",
    "he_thrown", "molotovs_thrown", "smokes_thrown", "smokes_detonated", "he_damage", "fire_damage",
    "enemies_flashed", "flash_seconds", "plants", "defuses",
]
WEAPON_NAMES = {
    "ak47": "AK-47", "m4a1": "M4A4", "m4a1_silencer": "M4A1-S", "awp": "AWP", "ssg08": "SSG 08",
    "deagle": "Desert Eagle", "glock": "Glock-18", "usp_silencer": "USP-S", "hkp2000": "P2000",
    "p250": "P250", "fiveseven": "Five-SeveN", "tec9": "Tec-9", "cz75a": "CZ75-Auto", "elite": "Dual Berettas",
    "revolver": "R8", "galilar": "Galil AR", "famas": "FAMAS", "aug": "AUG", "sg556": "SG 553",
    "mac10": "MAC-10", "mp9": "MP9", "mp7": "MP7", "mp5sd": "MP5-SD", "ump45": "UMP-45", "p90": "P90",
    "bizon": "PP-Bizon", "nova": "Nova", "xm1014": "XM1014", "mag7": "MAG-7", "sawedoff": "Sawed-Off",
    "m249": "M249", "negev": "Negev", "scar20": "SCAR-20", "g3sg1": "G3SG1", "hegrenade": "Granada HE",
    "inferno": "Molotov / incendiária", "taser": "Zeus x27",
}
CLASS_LABELS = [
    ("rifle_kills", "Rifles"), ("sniper_kills", "Snipers"), ("smg_kills", "SMGs"),
    ("pistol_kills", "Pistolas"), ("grenade_kills", "Granadas"), ("other_kills", "Outras"),
]


def _div(a, b):
    return a / b if b else None


def _num(value) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def aggregate(rows: list[dict]) -> dict:
    """Soma as contagens de todas as partidas com demo."""
    total: dict = {f: 0.0 for f in SUM_FIELDS}
    weapons: dict[str, int] = defaultdict(int)
    clutches = {f"1v{n}": [0, 0] for n in range(1, 6)}
    for row in rows:
        for field in SUM_FIELDS:
            total[field] += _num(row.get(field))
        for weapon, count in (row.get("weapon_kills") or {}).items():
            weapons[weapon] += int(count)
        for key, pair in (row.get("clutches") or {}).items():
            if key in clutches and len(pair) == 2:
                clutches[key][0] += int(pair[0])
                clutches[key][1] += int(pair[1])
    total["maps"] = len(rows)
    total["weapons"] = dict(weapons)
    total["clutch_table"] = clutches
    return total


def _side(t: dict, name: str, side: str | None) -> float:
    if side is None:
        return t[f"{name}_t"] + t[f"{name}_ct"]
    return t[f"{name}_{side}"]


def rating1(t: dict, side: str | None = None) -> float | None:
    """Rating 1.0 da HLTV: (kill + 0,7 sobrevivência + multi-kill) / 2,7."""
    rounds = _side(t, "rounds", side)
    if not rounds:
        return None
    kills, deaths = _side(t, "kills", side), _side(t, "deaths", side)
    multi = sum(n * n * _side(t, f"rk{n}", side) for n in range(1, 6))
    return ((kills / rounds) / 0.679 + 0.7 * ((rounds - deaths) / rounds) / 0.317 + (multi / rounds) / 1.277) / 2.7


def rating2(t: dict, side: str | None = None) -> float | None:
    """Rating 2.0 da HLTV (fórmula pública de 2017). Estimativa: o SCOPE usa variação própria."""
    rounds = _side(t, "rounds", side)
    if not rounds:
        return None
    kpr, dpr = _side(t, "kills", side) / rounds, _side(t, "deaths", side) / rounds
    apr = _side(t, "assists", side) / rounds
    kast = _side(t, "kast_rounds", side) / rounds * 100
    adr = _side(t, "damage", side) / rounds
    impact = 2.13 * kpr + 0.42 * apr - 0.41
    return 0.0073 * kast + 0.3591 * kpr - 0.5329 * dpr + 0.2372 * impact + 0.0032 * adr + 0.1587


def _m(key, value, t=None, ct=None, unit="n", decimals=2, hint="", adapted=False):
    label, meaning = METRIC_NAMES[key]
    return {"key": key, "label": label, "meaning": meaning, "value": value, "t": t, "ct": ct, "unit": unit,
            "decimals": decimals, "hint": hint, "adapted": adapted}


def _pct(v):
    return None if v is None else v * 100


def _by_side(fn):
    return fn(None), fn("t"), fn("ct")


def sections(t: dict) -> dict[str, list[dict]]:
    """Todas as métricas por seção, na ordem da página da HLTV."""
    def rate(name, side):
        return _div(_side(t, name, side), _side(t, "rounds", side))

    def per_round(name):
        v, a, b = _by_side(lambda s: rate(name, s))
        return v, a, b

    def multi_rounds(side):
        return sum(_side(t, f"rk{n}", side) for n in range(2, 6))

    def any_kill_rounds(side):
        return sum(_side(t, f"rk{n}", side) for n in range(1, 6))

    def opening_attempts(side):
        return _div(_side(t, "opening_kills", side) + _side(t, "opening_deaths", side), _side(t, "rounds", side))

    def opening_success(side):
        total = _side(t, "opening_kills", side) + _side(t, "opening_deaths", side)
        return _div(_side(t, "opening_kills", side), total)

    def opening_ratio(side):
        return _div(_side(t, "opening_kills", side), _side(t, "opening_deaths", side))

    def post_plant(side):
        return _div(_side(t, "alive_post_plant", side), _side(t, "rounds_with_plant", side))

    rounds, kills, deaths = _side(t, "rounds", None), _side(t, "kills", None), _side(t, "deaths", None)
    tries = sum(p[0] for p in t["clutch_table"].values())
    kpr3 = _by_side(lambda s: rate("kills", s))
    dpr3 = _by_side(lambda s: rate("deaths", s))
    adr3 = _by_side(lambda s: rate("damage", s))
    out: dict[str, list[dict]] = {}
    out["firepower"] = [
        _m("kpr", *kpr3, decimals=2),
        _m("adr", *adr3, decimals=1),
        _m("kprw", _div(t["kills_in_won_rounds"], t["rounds_won"]), decimals=2,
           hint="Kills feitas em rounds que o time venceu, divididas pelos rounds vencidos."),
        _m("adr_won", _div(t["damage_in_won_rounds"], t["rounds_won"]), decimals=1,
           adapted=True, hint="Substitui o Round Win Shares da HLTV, cuja fórmula não é pública."),
        _m("rounds_with_kill", *[_pct(_div(any_kill_rounds(s), _side(t, "rounds", s))) for s in (None, "t", "ct")],
           unit="pct", decimals=1),
        _m("rounds_multikill", *[_pct(_div(multi_rounds(s), _side(t, "rounds", s))) for s in (None, "t", "ct")],
           unit="pct", decimals=1),
        _m("net_kills", *[_div((_side(t, "kills", s) - _side(t, "deaths", s)) * 24, _side(t, "rounds", s)) for s in (None, "t", "ct")],
           decimals=2, hint="(kills - mortes) / rounds x 24."),
        _m("net_damage", _div(t["damage_t"] + t["damage_ct"] - t["damage_taken"], rounds), decimals=1,
           adapted=True, hint="Dano causado menos dano recebido de inimigos, por round."),
        _m("headshots", _pct(_div(t["headshots"], kills)), unit="pct", decimals=1),
    ]
    out["entrying"] = [
        _m("dpr", *dpr3, decimals=2),
        _m("deaths_traded", _pct(_div(t["deaths_traded"], deaths)), unit="pct", decimals=1,
           hint="Mortes vingadas por um companheiro em até 5 segundos."),
        _m("apr", *[_div(_side(t, "assists", s), _side(t, "rounds", s)) for s in (None, "t", "ct")], decimals=2,
           hint="Assistências de dano, sem contar flash assist."),
        _m("opening_deaths_pr", *[_div(_side(t, "opening_deaths", s), _side(t, "rounds", s)) for s in (None, "t", "ct")], decimals=2),
    ]
    out["trading"] = [
        _m("trade_kills_pr", _div(t["trade_kills"], rounds), decimals=2),
        _m("trade_kills_pct", _pct(_div(t["trade_kills"], kills)), unit="pct", decimals=1,
           hint="Parte das kills que vingou uma morte de companheiro em até 5 segundos."),
        _m("assisted_kills", _pct(_div(t["assisted_kills"], kills)), unit="pct", decimals=1),
    ]
    out["opening"] = [
        _m("opening_attempts", *[_pct(opening_attempts(s)) for s in (None, "t", "ct")], unit="pct", decimals=1,
           hint="Rounds em que o jogador matou ou morreu primeiro."),
        _m("opening_kills", *[_side(t, "opening_kills", s) for s in (None, "t", "ct")], decimals=0),
        _m("opening_deaths", *[_side(t, "opening_deaths", s) for s in (None, "t", "ct")], decimals=0),
        _m("opening_ratio", *[opening_ratio(s) for s in (None, "t", "ct")], decimals=2),
        _m("opening_success", *[_pct(opening_success(s)) for s in (None, "t", "ct")], unit="pct", decimals=1),
        _m("win_after_opening", _pct(_div(t["opening_kill_rounds_won"], t["opening_kills_t"] + t["opening_kills_ct"])), unit="pct", decimals=1),
        _m("first_kill_won", _pct(_div(t["opening_kills_in_won_rounds"], t["rounds_won"])), unit="pct", decimals=1,
           hint="Kills de abertura em rounds vencidos, divididas pelos rounds vencidos."),
    ]
    out["closing"] = [
        _m("time_alive", _div(t["time_alive_seconds"], rounds), unit="s", decimals=0,
           hint="Do fim do tempo de compra até a morte ou o fim do round."),
        _m("post_plant", *[_pct(post_plant(s)) for s in (None, "t", "ct")], unit="pct", decimals=1,
           adapted=True, hint="Dos rounds com bomba plantada, quantos o jogador ainda estava vivo."),
        _m("last_alive", _pct(_div(t["last_alive_rounds"], rounds)), unit="pct", decimals=1,
           hint="Rounds em que ficou sozinho contra pelo menos um inimigo."),
        _m("clutches_24", _div(t["clutches_won"] * 24, rounds), decimals=2),
        _m("clutch_win", _pct(_div(t["clutches_won"], tries)), unit="pct", decimals=1),
    ]
    out["sniping"] = [
        _m("rounds_sniper", _pct(_div(t["rounds_with_sniper"], rounds)), unit="pct", decimals=1),
        _m("sniper_kills", _pct(_div(t["sniper_kills"], kills)), unit="pct", decimals=1),
        _m("rounds_awp", _pct(_div(t["rounds_with_awp"], rounds)), unit="pct", decimals=1),
        _m("awp_kills", _pct(_div(t["awp_kills"], kills)), unit="pct", decimals=1),
    ]
    out["utility"] = [
        _m("util_damage", _div(t["he_damage"] + t["fire_damage"], rounds), decimals=1),
        _m("he_damage", _div(t["he_damage"], rounds), decimals=1),
        _m("fire_damage", _div(t["fire_damage"], rounds), decimals=1),
        _m("flashes", _div(t["flashes_thrown"], rounds), decimals=2),
        _m("flash_assists", _div(t["flash_assists"], rounds), decimals=2),
        _m("flashed", _div(t["enemies_flashed"], rounds), decimals=2),
        _m("flash_time", _div(t["flash_seconds"], rounds), unit="s", decimals=1),
        _m("smokes", _div(t["smokes_detonated"], rounds), decimals=2),
    ]
    return out


# Componentes de cada nota 0 a 100: (chave da métrica, sinal). Sinal -1 = quanto menor, melhor.
SCORE_PARTS = {
    "firepower": [("kpr", 1), ("adr", 1), ("kprw", 1), ("rounds_multikill", 1)],
    "entrying": [("deaths_traded", 1), ("apr", 1), ("dpr", -1)],
    "trading": [("trade_kills_pct", 1), ("assisted_kills", 1)],
    "opening": [("opening_attempts", 1), ("opening_success", 1)],
    "closing": [("clutches_24", 1), ("time_alive", 1), ("post_plant", 1)],
    "sniping": [("sniper_kills", 1), ("rounds_sniper", 1)],
    "utility": [("flash_assists", 1), ("flashed", 1), ("util_damage", 1)],
}


def _percentile(value: float, others: list[float]) -> float:
    below = sum(1 for o in others if o < value)
    equal = sum(1 for o in others if o == value)
    return 100 * (below + 0.5 * equal) / len(others)


def percentile_scores(profiles: dict[str, dict]) -> dict[str, dict[str, int | None]]:
    """Nota 0 a 100 por seção: posição do jogador entre quem tem demo na liga."""
    flat = {pid: {m["key"]: m["value"] for ms in p["sections"].values() for m in ms} for pid, p in profiles.items()}
    scores: dict[str, dict[str, int | None]] = {pid: {} for pid in profiles}
    for section, parts in SCORE_PARTS.items():
        for pid in profiles:
            values = []
            for key, sign in parts:
                mine = flat[pid].get(key)
                pool = [f[key] for f in flat.values() if f.get(key) is not None]
                if mine is None or len(pool) < 3:
                    continue
                pool = pool if sign > 0 else [-v for v in pool]
                values.append(_percentile(mine if sign > 0 else -mine, pool))
            scores[pid][section] = round(sum(values) / len(values)) if values else None
    return scores


SIDES = (None, "t", "ct")


def _card(key, label, meaning, value, unit="n", decimals=2):
    return {"key": key, "label": label, "meaning": meaning, "value": value, "unit": unit, "decimals": decimals}


def empty_profile(side: str | None = None) -> dict:
    """Perfil sem nenhuma linha: mesma forma do perfil real, com contagens zeradas e valores nulos."""
    none = {k: None for k in ("rating1", "rating1_t", "rating1_ct", "rating2", "rating2_t", "rating2_ct")}
    return {
        "rounds": 0, "side": side or "all", "rating": none, "cards": [], "sections": {k: [] for k in SECTION_ORDER},
        "multikills": [], "clutches": [], "weapon_classes": [], "weapons": [], "special_kills": [],
        "totals": {"kills": 0, "deaths": 0, "assists": 0, "rounds_with_kill": 0, "plants": 0, "defuses": 0,
                   "kills_t": 0, "kills_ct": 0},
        "scores": [], "similar": [],
    }


def build_profile(rows: list[dict], side: str | None = None) -> dict | None:
    """Perfil de um jogador a partir das linhas dele em player_match_detail.

    ``side`` ("t" ou "ct") restringe ao lado escolhido tudo o que a demo separa por lado. O que a demo
    não separa (armas, clutches, métricas sem T e CT) fica sem valor no lado, em vez de mostrar o total.
    """
    if not rows:
        return None
    t = aggregate(rows)
    rounds = _side(t, "rounds", side)
    if not rounds:
        return None
    kills = _side(t, "kills", side)
    sects = sections(t)
    if side:
        sects = {k: [{**m, "value": m[side]} for m in v] for k, v in sects.items()}
    return {
        "rounds": int(rounds),
        "side": side or "all",
        "rating": {
            "rating1": _round(rating1(t, side)), "rating1_t": _round(rating1(t, "t")), "rating1_ct": _round(rating1(t, "ct")),
            "rating2": _round(rating2(t, side)), "rating2_t": _round(rating2(t, "t")), "rating2_ct": _round(rating2(t, "ct")),
        },
        "cards": [
            _card("rating1_t", "T Rating", "Rating 1.0 jogando de T", _round(rating1(t, "t"))),
            _card("rating1", "Rating 1.0", "rating geral" if not side else "rating no lado", _round(rating1(t, side))),
            _card("rating1_ct", "CT Rating", "Rating 1.0 jogando de CT", _round(rating1(t, "ct"))),
            _card("dpr", "DPR", "mortes por round", _round(_div(_side(t, "deaths", side), rounds))),
            _card("kast", "KAST", "rounds com kill, assistência, sobrevivência ou troca",
                  _round(_pct(_div(_side(t, "kast_rounds", side), rounds)), 1), "pct", 1),
            _card("multikill", "Multi-kill", "rounds com 2 ou mais kills",
                  _round(_pct(_div(sum(_side(t, f"rk{n}", side) for n in range(2, 6)), rounds)), 1), "pct", 1),
            _card("adr", "ADR", "dano médio por round", _round(_div(_side(t, "damage", side), rounds), 1), "n", 1),
            _card("kpr", "KPR", "kills por round", _round(_div(kills, rounds))),
        ],
        "sections": {k: [_clean(m) for m in v] for k, v in sects.items()},
        "multikills": [
            {"kills": n, "rounds": int(_side(t, f"rk{n}", side)), "t": int(t[f"rk{n}_t"]), "ct": int(t[f"rk{n}_ct"]),
             "pct": _round(_pct(_div(_side(t, f"rk{n}", side), rounds)), 1)} for n in range(1, 6)
        ],
        "clutches": [
            {"label": f"1v{n}", "tries": t["clutch_table"][f"1v{n}"][0], "won": t["clutch_table"][f"1v{n}"][1]}
            for n in range(1, 6)
        ],
        "weapon_classes": [
            {"label": label, "kills": int(t[field]), "pct": _round(_pct(_div(t[field], _side(t, "kills", None))), 1)}
            for field, label in CLASS_LABELS
        ],
        "weapons": [
            {"weapon": WEAPON_NAMES.get(w, w.replace("_", " ")), "kills": c,
             "pct": _round(_pct(_div(c, _side(t, "kills", None))), 1)}
            for w, c in sorted(t["weapons"].items(), key=lambda kv: -kv[1])[:10]
        ],
        "special_kills": [
            {"label": "Pela fumaça", "kills": int(t["smoke_kills"])}, {"label": "Por parede", "kills": int(t["wallbang_kills"])},
            {"label": "Sem mira (noscope)", "kills": int(t["noscope_kills"])}, {"label": "Cego", "kills": int(t["blind_kills"])},
        ],
        "totals": {
            "kills": int(kills), "deaths": int(_side(t, "deaths", side)), "assists": int(_side(t, "assists", side)),
            "rounds_with_kill": int(sum(_side(t, f"rk{n}", side) for n in range(1, 6))),
            "plants": int(t["plants"]), "defuses": int(t["defuses"]),
            "kills_t": int(t["kills_t"]), "kills_ct": int(t["kills_ct"]),
        },
    }


def _round(value, digits: int = 2):
    return None if value is None else round(value, digits)


def _clean(metric: dict) -> dict:
    d = metric["decimals"]
    return {**metric, "value": _round(metric["value"], d + 1), "t": _round(metric["t"], d + 1), "ct": _round(metric["ct"], d + 1)}


def build_league(rows_by_player: dict[str, list[dict]], side: str | None = None) -> dict[str, dict]:
    """Perfis de todos os jogadores com demo, já com as notas 0 a 100 e jogadores parecidos."""
    profiles = {pid: p for pid, rows in rows_by_player.items() if (p := build_profile(rows, side))}
    scores = percentile_scores(profiles)
    for pid, profile in profiles.items():
        profile["scores"] = [
            {"key": s, "label": SECTION_LABELS[s][0], "meaning": SECTION_LABELS[s][1], "value": scores[pid].get(s)}
            for s in SECTION_ORDER
        ]
    for pid, profile in profiles.items():
        mine = [s["value"] for s in profile["scores"]]
        similar = []
        for other, p2 in profiles.items():
            if other == pid:
                continue
            theirs = [s["value"] for s in p2["scores"]]
            pairs = [(a, b) for a, b in zip(mine, theirs) if a is not None and b is not None]
            if len(pairs) < 4:
                continue
            distance = (sum((a - b) ** 2 for a, b in pairs) / len(pairs)) ** 0.5
            similar.append({"player_id": other, "similarity": round(max(0.0, 100 - distance))})
        profile["similar"] = sorted(similar, key=lambda s: -s["similarity"])[:3]
    return profiles
