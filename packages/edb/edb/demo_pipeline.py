"""Pipeline de importação de demos (.dem / .dem.gz / .gz) para a EDB LEAGUE.

Nome do arquivo: ``<mdN>_<mapa>_<dd>_<mm>[_<n>].dem``

- ``md1`` ou ``md3`` define o formato da série.
- ``mapa`` é conferido com o mapa que está dentro da demo.
- ``dd_mm`` é a data (a demo não traz data). O ano é o atual; datas futuras caem no ano anterior.
- ``n``: em md3, a ordem do mapa na série (1 a 3, obrigatório). Em md1, só desambigua
  duas partidas do mesmo dia (padrão 1).

Este módulo não faz rede nem lê variáveis de ambiente: a parte de gravação recebe um ``Store``.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import re
import tempfile
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

from edb.demo_stats import COUNT_FIELDS, PARSER_VERSION
from edb.hltv_stats import rating2

MAX_UNCOMPRESSED = 1024 * 1024 * 1024  # 1 GB
KNOWN_MAPS = {
    "ancient", "anubis", "dust2", "inferno", "mirage", "nuke", "overpass", "train", "vertigo",
    "cache", "cobblestone", "office", "italy", "agency",
}
_NAME = re.compile(r"^(md[13])_([a-z0-9]+)_(\d{1,2})_(\d{1,2})(?:_(\d{1,2}))?$", re.IGNORECASE)
EXAMPLE = "md3_inferno_20_10_1.dem"


# --------------------------------------------------------------------------- nome do arquivo
@dataclass(frozen=True)
class DemoFile:
    path: Path
    fmt: str            # "bo1" | "bo3"
    map: str            # "inferno"
    played_on: date
    order: int          # 1..3 em bo3; 1 em bo1 (ou o número do dia)


def _stem(name: str) -> str:
    low = name.lower()
    for ext in (".dem.gz", ".dem", ".gz"):
        if low.endswith(ext):
            return name[: -len(ext)]
    raise ValueError(f"{name}: use a extensão .dem, .dem.gz ou .gz.")


def parse_filename(path: str | Path, today: date | None = None) -> DemoFile:
    path = Path(path)
    today = today or date.today()
    found = _NAME.match(_stem(path.name))
    if not found:
        raise ValueError(f"{path.name}: nome fora do padrão. Exemplo: {EXAMPLE}")
    kind, map_name, day, month, order = found.groups()
    map_name = map_name.lower()
    if map_name not in KNOWN_MAPS:
        raise ValueError(f"{path.name}: mapa '{map_name}' desconhecido ({', '.join(sorted(KNOWN_MAPS))}).")
    fmt = "bo3" if kind.lower() == "md3" else "bo1"
    if fmt == "bo3":
        if order is None or not 1 <= int(order) <= 3:
            raise ValueError(f"{path.name}: em md3 informe a ordem do mapa no fim (_1, _2 ou _3). Exemplo: {EXAMPLE}")
        number = int(order)
    else:
        number = int(order) if order else 1
    try:
        played = date(today.year, int(month), int(day))
    except ValueError:
        raise ValueError(f"{path.name}: data {day}/{month} inválida.") from None
    if played > today + timedelta(days=1):
        played = date(today.year - 1, int(month), int(day))
    return DemoFile(path, fmt, map_name, played, number)


# --------------------------------------------------------------------------- leitura da demo
def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def analyze_file(path: str | Path, cache_dir: str | Path | None = None) -> tuple[str, dict]:
    """Devolve (sha256, análise). O resultado fica em cache para não reprocessar a demo."""
    from edb.demo_stats import analyze

    path = Path(path)
    sha = sha256_file(path)
    cache = Path(cache_dir) / f"{sha}.v{PARSER_VERSION}.json" if cache_dir else None
    if cache and cache.exists():
        return sha, json.loads(cache.read_text(encoding="utf-8"))
    if path.name.lower().endswith(".gz"):
        with tempfile.TemporaryDirectory(prefix="edb_demo_") as tmp:
            out, size = Path(tmp) / "partida.dem", 0
            with gzip.open(path, "rb") as src, open(out, "wb") as dest:
                for block in iter(lambda: src.read(8 * 1024 * 1024), b""):
                    size += len(block)
                    if size > MAX_UNCOMPRESSED:
                        raise ValueError(f"{path.name}: demo descompactada passa de 1 GB.")
                    dest.write(block)
            result = analyze(str(out))
    else:
        result = analyze(str(path))
    if cache:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(result), encoding="utf-8")
    return sha, result


@dataclass
class DemoRun:
    file: DemoFile
    sha: str
    analysis: dict
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def roster(self) -> frozenset[str]:
        return frozenset(str(p["steamid"]) for p in self.analysis["players"])

    @property
    def sides(self) -> tuple[set[str], set[str]]:
        r = self.analysis["rosters"]
        return {str(s) for s in r["team_t_first"]}, {str(s) for s in r["team_ct_first"]}


def check_demo(file: DemoFile, analysis: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    name = file.path.name
    if str(analysis.get("map", "")).lower() != file.map:
        errors.append(f"{name}: o nome diz {file.map}, mas a demo é de {analysis.get('map') or '?'}.")
    ids = [str(p.get("steamid") or "") for p in analysis["players"]]
    if len(ids) != 10 or len(set(ids)) != 10 or not all(ids):
        errors.append(f"{name}: a demo tem {len(ids)} jogadores; são necessários 10 SteamIDs distintos (5v5).")
    score = analysis["score"]
    t_first, ct_first = int(score["team_t_first"]), int(score["team_ct_first"])
    if t_first + ct_first != int(analysis["rounds"]):
        errors.append(f"{name}: placar {t_first}x{ct_first} não soma os {analysis['rounds']} rounds.")
    if t_first == ct_first:
        errors.append(f"{name}: placar empatado ({t_first}x{ct_first}).")
    if max(t_first, ct_first) < 13:
        warnings.append(f"{name}: ninguém chegou a 13 rounds ({t_first}x{ct_first}); confira se a partida acabou antes.")
    return errors, warnings


# --------------------------------------------------------------------------- séries
@dataclass
class Series:
    fmt: str
    played_on: date
    demos: list[DemoRun]
    problems: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return not self.problems and all(not d.errors for d in self.demos)

    @property
    def label(self) -> str:
        maps = ", ".join(d.file.map for d in self.demos)
        return f"{self.fmt.upper()} {self.played_on:%d/%m/%Y} ({maps})"


MIN_SHARED_PLAYERS = 6   # abaixo disso entre mapas seguidos, a prévia avisa que o elenco mudou muito


def group_series(runs: list[DemoRun]) -> list[Series]:
    """Agrupa as demos em confrontos.

    md1: um confronto por demo. md3: as demos do mesmo dia com ordens 1, 2 e 3 formam uma série mesmo que
    algum jogador entre ou saia no meio. Só quando há mais de três md3 no dia (duas séries) o agrupamento
    usa o elenco para separá-las.
    """
    series: list[Series] = []
    by_day: dict[date, list[DemoRun]] = {}
    for run in runs:
        if run.file.fmt == "bo1":
            series.append(Series("bo1", run.file.played_on, [run]))
        else:
            by_day.setdefault(run.file.played_on, []).append(run)
    for played, day_runs in by_day.items():
        orders = [r.file.order for r in day_runs]
        if len(day_runs) <= 3 and len(set(orders)) == len(orders):
            groups = [day_runs]
        else:
            split: dict[frozenset, list[DemoRun]] = {}
            for run in day_runs:
                split.setdefault(run.roster, []).append(run)
            groups = list(split.values())
        for items in groups:
            items.sort(key=lambda r: r.file.order)
            s = Series("bo3", played, items)
            orders = [r.file.order for r in items]
            if len(set(orders)) != len(orders):
                s.problems.append("Há dois arquivos com a mesma ordem na série (mesmos jogadores e data).")
            elif orders != [1, 2, 3]:
                missing = [str(n) for n in (1, 2, 3) if n not in orders]
                s.problems.append(f"Série incompleta: faltam os mapas de ordem {', '.join(missing)}.")
            if len({r.file.map for r in items}) != len(items):
                s.problems.append("A série repete o mesmo mapa.")
            for before, after in zip(items, items[1:]):
                shared = len(before.roster & after.roster)
                if shared < MIN_SHARED_PLAYERS:
                    s.notes.append(f"Só {shared} jogadores repetem de {before.file.path.name} para {after.file.path.name}; "
                                   "confira se são mesmo a mesma série.")
            series.append(s)
    series.sort(key=lambda s: (s.played_on, s.demos[0].file.path.name))
    return series


# Regra da liga: PT é o time em que está o jogador-âncora de PT; PL, o da âncora de PL.
# Cada âncora aceita nick da demo, nick/alias do banco ou SteamID.
DEFAULT_ANCHORS = {"PT": ["Neteb", "Петэв", "Pyetev"], "PL": ["The Most", "Scby"]}


def anchor_steamids(terms: list[str], series: Series, directory: "Directory | None" = None) -> set[str]:
    """SteamIDs da série que correspondem aos termos (nick na demo, nick/alias no banco ou SteamID)."""
    wanted = {str(t).strip().casefold() for t in terms if str(t).strip()}
    found: set[str] = set()
    roster: set[str] = set()
    for run in series.demos:
        for p in run.analysis["players"]:
            steam = str(p["steamid"])
            roster.add(steam)
            if steam.casefold() in wanted or str(p.get("nick") or "").casefold() in wanted:
                found.add(steam)
    if directory:
        for term in wanted:
            for pid in directory.by_name.get(term, ()):
                steam = str(directory.players[pid].get("steamid") or "")
                if steam in roster:
                    found.add(steam)
    return found


def assign_teams(series: Series, swap: bool = False, anchors: dict[str, set[str]] | None = None):
    """Define o time A (PT) de cada mapa e os placares A x B. Devolve (conjuntos A por mapa, placares, base).

    Regra por mapa, na ordem:
    1. âncora de PT e âncora de PL no mesmo time: esse time é PT;
    2. só a âncora de PT joga: o time dela é PT;
    3. só a âncora de PL joga: o time oposto é PT;
    4. nenhuma âncora: o time com mais jogadores do PT do mapa anterior (ou, no primeiro mapa, quem começou de T).
    Jogadores podem entrar e sair entre mapas, mas ninguém pode jogar pelos dois times na mesma série.
    """
    pt = (anchors or {}).get("PT", set())
    pl = (anchors or {}).get("PL", set())
    a_sets: list[set[str]] = []
    scores: list[tuple[int, int]] = []
    bases: list[str] = []
    for run in series.demos:
        t_set, ct_set = run.sides
        pt_in = "t" if pt & t_set else "ct" if pt & ct_set else None
        pl_in = "t" if pl & t_set else "ct" if pl & ct_set else None
        if pt_in and pl_in and pt_in == pl_in:
            side, basis = pt_in, "âncoras de PT e PL juntas: esse time é PT"
        elif pt_in:
            side, basis = pt_in, "time da âncora de PT"
        elif pl_in:
            side, basis = ("ct" if pl_in == "t" else "t"), "oposto da âncora de PL"
        elif a_sets:
            side = "t" if len(t_set & a_sets[-1]) >= len(ct_set & a_sets[-1]) else "ct"
            basis = "continuidade com o mapa anterior (sem âncora neste mapa)"
        else:
            side, basis = "t", "quem começou de T no primeiro mapa (nenhuma âncora na série)"
        if swap and not basis.startswith("continuidade"):   # a continuidade já parte do time invertido
            side = "ct" if side == "t" else "t"
            basis += " (invertido por --trocar-times)"
        a_set = set(t_set if side == "t" else ct_set)
        t_score, ct_score = int(run.analysis["score"]["team_t_first"]), int(run.analysis["score"]["team_ct_first"])
        scores.append((t_score, ct_score) if side == "t" else (ct_score, t_score))
        a_sets.append(a_set)
        if basis not in bases:
            bases.append(basis)
    in_a = set().union(*a_sets)
    in_b = set().union(*(run.roster - a for run, a in zip(series.demos, a_sets)))
    if in_a & in_b:
        raise ValueError("O mesmo jogador aparece nos dois times da série "
                         f"({', '.join(sorted(in_a & in_b))}); confira o nome dos arquivos e as âncoras.")
    return a_sets, scores, "; ".join(bases)


def roster_changes(series: Series, a_sets: list[set[str]]) -> list[tuple[int, str, set[str], set[str]]]:
    """(índice do mapa, time 'A'/'B', quem entrou, quem saiu) em relação ao mapa anterior."""
    out = []
    for i in range(1, len(series.demos)):
        for label, now, before in (
            ("A", a_sets[i], a_sets[i - 1]),
            ("B", series.demos[i].roster - a_sets[i], series.demos[i - 1].roster - a_sets[i - 1]),
        ):
            if now != before:
                out.append((i, label, now - before, before - now))
    return out


# --------------------------------------------------------------------------- identidades
class Directory:
    """Liga SteamIDs aos jogadores do banco. SteamID é automático; nick só vira sugestão."""

    def __init__(self, players: list[dict], aliases: list[dict] | None = None):
        self.players = {str(p["id"]): p for p in players}
        self.by_steam = {str(p["steamid"]): str(p["id"]) for p in players if p.get("steamid")}
        # Segunda conta: um alias que é um SteamID (só dígitos) liga essa conta ao jogador.
        for a in aliases or []:
            key = str(a["alias"]).strip()
            if key.isdigit() and len(key) >= 15:
                self.by_steam.setdefault(key, str(a["player_id"]))
        self.by_name: dict[str, set[str]] = {}
        for p in players:
            self.by_name.setdefault(str(p["nickname"]).casefold(), set()).add(str(p["id"]))
        for a in aliases or []:
            self.by_name.setdefault(str(a["alias"]).casefold(), set()).add(str(a["player_id"]))

    def resolve(self, steamid: str) -> str | None:
        return self.by_steam.get(str(steamid))

    def suggest(self, nick: str) -> str | None:
        """Jogador sem SteamID cadastrado cujo nick ou alias bate exatamente com o da demo."""
        found = [pid for pid in self.by_name.get(str(nick).casefold(), ())
                 if not self.players[pid].get("steamid")]
        return found[0] if len(found) == 1 else None

    def name(self, player_id: str) -> str:
        return str(self.players[player_id]["nickname"])


def demo_nicks(series: Series) -> dict[str, str]:
    out: dict[str, str] = {}
    for run in series.demos:
        for p in run.analysis["players"]:
            out[str(p["steamid"])] = str(p.get("nick") or "")
    return out


# --------------------------------------------------------------------------- linhas do banco
def season_for(seasons: list[dict], played_on: date) -> dict:
    for s in seasons:
        if int(s["number"]) < 1 or not s.get("starts_on") or not s.get("ends_on"):
            continue
        if str(s["starts_on"])[:10] <= played_on.isoformat() <= str(s["ends_on"])[:10]:
            if s.get("homologated_at"):
                raise ValueError(f"A temporada {s['number']} já foi homologada; não aceita novas partidas.")
            return s
    raise ValueError(f"Nenhuma temporada aberta cobre {played_on:%d/%m/%Y}.")


def stats_row(match_id: str, player_id: str, p: dict) -> dict:
    est = rating2({f: p.get(f, 0) for f in COUNT_FIELDS})
    return {
        "match_id": match_id, "player_id": player_id,
        "kills": p["kills"], "deaths": p["deaths"], "assists": p["assists"],
        "damage": p["damage"], "rounds": p["rounds"], "won": None, "headshots": p["headshots"],
        "plants": p["plants"], "defuses": p["defuses"],
        "rating": round(est, 2) if est is not None else None,
        "kast": p["kast"], "open_kills": p["open_kills"], "trade_kills": p["trade_kills"],
        "observed_nickname": str(p.get("nick") or "") or None,
    }


def detail_row(match_id: str, player_id: str, p: dict) -> dict:
    row = {"match_id": match_id, "player_id": player_id}
    row.update({f: p[f] for f in COUNT_FIELDS})
    row["weapon_kills"] = p.get("weapon_kills") or {}
    row["clutches"] = p.get("clutches") or {}
    row["parser_version"] = PARSER_VERSION
    return row


def scope_row(match_id: str, player_id: str, p: dict) -> dict:
    """Só o que a demo mede de utilitários. Mira e ADR oficial ficam nulos (não existem na demo)."""
    return {
        "match_id": match_id, "player_id": player_id,
        "flash_assists": p["flash_assists"], "enemies_flashed": p["enemies_flashed"],
        "total_flash_duration_seconds": p["flash_seconds"],
        "grenade_damage": p["he_damage"] + p["fire_damage"], "smokes_used": p["smokes_thrown"],
    }


def match_row(match_id: str, run: DemoRun, played_on: date) -> dict:
    server = str(run.analysis.get("server") or "").strip()
    return {
        "id": match_id, "played_at": played_on.isoformat(), "map_name": run.file.map.title(),
        "source": "Demo CS2" + (f" - {server}" if server else ""), "rounds_total": int(run.analysis["rounds"]),
        "notes": f"sha256:{run.sha}; arquivo:{run.file.path.name}; parser v{PARSER_VERSION}",
    }


def build_plan(series: Series, season: dict, match_ids: list[str], ids: dict[str, str],
               team_a_name: str, team_b_name: str, swap: bool = False,
               anchors: dict[str, set[str]] | None = None) -> dict:
    """Tudo o que será gravado, pronto para a prévia e para o Store."""
    a_sets, scores, _ = assign_teams(series, swap, anchors)
    plan = {"matches": [], "player_stats": [], "details": [], "scope": [], "bundle": None}
    for run, mid in zip(series.demos, match_ids):
        plan["matches"].append(match_row(mid, run, series.played_on))
        for p in run.analysis["players"]:
            pid = ids[str(p["steamid"])]
            plan["player_stats"].append(stats_row(mid, pid, p))
            plan["details"].append(detail_row(mid, pid, p))
            plan["scope"].append(scope_row(mid, pid, p))
    plan["bundle"] = {
        "season_number": int(season["number"]), "format": series.fmt,
        "team_a_name": team_a_name, "team_b_name": team_b_name,
        "team_a_player_ids": sorted(ids[s] for s in a_sets[0]),
        "matches": [{"match_id": mid, "team_a_score": a, "team_b_score": b,
                     "team_a_player_ids": sorted(ids[s] for s in a_set)}
                    for mid, (a, b), a_set in zip(match_ids, scores, a_sets)],
    }
    return plan


def next_match_ids(series: Series, season: dict, existing_series: list[dict], taken: set[str],
                   reserved: int = 0) -> list[str]:
    """IDs no padrão edb-t1-bo3-02-mirage. O contador é por temporada e formato."""
    number = int(season["number"])
    count = sum(1 for s in existing_series
                if int(s["season_number"]) == number and str(s.get("match_format") or "bo3") == series.fmt)
    n = count + 1 + reserved
    while True:
        ids = [f"edb-t{number}-{series.fmt}-{n:02d}-{r.file.map}" for r in series.demos]
        if not any(i in taken for i in ids):
            return ids
        n += 1


def find_existing_series(series: Series, ids: dict[str, str], matches: list[dict],
                         stats: list[dict]) -> list[str]:
    """Partidas já no banco com o mesmo mapa, os mesmos 10 jogadores e data a até 1 dia de distância.

    Evita duplicar uma partida cadastrada antes pelos prints do SCOPE (sem hash de demo).
    """
    by_match: dict[str, set[str]] = {}
    for row in stats:
        by_match.setdefault(str(row["match_id"]), set()).add(str(row["player_id"]))
    found = []
    for run in series.demos:
        roster = {ids[str(p["steamid"])] for p in run.analysis["players"]}
        for m in matches:
            if str(m.get("map_name") or "").casefold() != run.file.map:
                continue
            if abs((date.fromisoformat(str(m["played_at"])[:10]) - series.played_on).days) > 1:
                continue
            if by_match.get(str(m["id"])) == roster:
                found.append(str(m["id"]))
    return found


def existing_by_demo(series: Series, ids: dict[str, str], matches: list[dict], stats: list[dict]) -> dict[int, str]:
    """Posição da demo na série -> id da partida que já está no banco (mesmo critério de find_existing_series)."""
    by_match: dict[str, set[str]] = {}
    for row in stats:
        by_match.setdefault(str(row["match_id"]), set()).add(str(row["player_id"]))
    found: dict[int, str] = {}
    for index, run in enumerate(series.demos):
        roster = {ids[str(p["steamid"])] for p in run.analysis["players"]}
        for m in matches:
            if str(m.get("map_name") or "").casefold() != run.file.map:
                continue
            if abs((date.fromisoformat(str(m["played_at"])[:10]) - series.played_on).days) > 1:
                continue
            if by_match.get(str(m["id"])) == roster and str(m["id"]) not in found.values():
                found[index] = str(m["id"])
                break
    return found


def completion_plan(series: Series, ids: dict[str, str], existing: dict[int, str], matches: list[dict],
                    with_details: set[str]) -> dict:
    """Só os detalhes da demo para partidas que já existem no banco sem eles (ex.: cadastradas pelo SCOPE).

    Não mexe em placar, times, estatísticas nem série: apenas acrescenta ``player_match_detail`` e registra
    o hash da demo nas notas da partida, para ela não ser lida de novo.
    """
    notes_by_id = {str(m["id"]): str(m.get("notes") or "") for m in matches}
    plan: dict = {"details": [], "notes": {}, "match_ids": []}
    for index, match_id in sorted(existing.items()):
        if match_id in with_details:
            continue
        run = series.demos[index]
        for p in run.analysis["players"]:
            plan["details"].append(detail_row(match_id, ids[str(p["steamid"])], p))
        tag = f"demo sha256:{run.sha}; arquivo:{run.file.path.name}; parser v{PARSER_VERSION}"
        old = notes_by_id.get(match_id, "")
        plan["notes"][match_id] = f"{old}; {tag}" if old else tag
        plan["match_ids"].append(match_id)
    return plan


def write_completion(store, plan: dict, old_notes: dict[str, str]) -> None:
    """Grava os detalhes e as notas. Se algo falhar, remove o que acabou de gravar."""
    done: list[str] = []
    try:
        store._api("POST", "player_match_detail", params={"on_conflict": "match_id,player_id"}, payload=plan["details"])
        for match_id, notes in plan["notes"].items():
            store._api("PATCH", "matches", params={"id": f"eq.{match_id}"}, payload={"notes": notes})
            done.append(match_id)
    except Exception:
        ids = "in.(" + ",".join(plan["match_ids"]) + ")"
        try:
            store._api("DELETE", "player_match_detail", params={"match_id": ids})
        except Exception:  # noqa: BLE001 - desfazer é melhor esforço; o erro original segue
            pass
        for match_id in done:
            try:
                store._api("PATCH", "matches", params={"id": f"eq.{match_id}"}, payload={"notes": old_notes.get(match_id) or None})
            except Exception:  # noqa: BLE001
                pass
        raise


# --------------------------------------------------------------------------- gravação
def write_steam_aliases(store, extra: dict[str, str]) -> list[str]:
    """Grava em player_aliases as segundas contas ({steamid: player_id}). Devolve os aliases criados."""
    created: list[str] = []
    try:
        for steamid, player_id in extra.items():
            store._api("POST", "player_aliases", params={"on_conflict": "alias"},
                       payload={"alias": str(steamid), "player_id": str(player_id)})
            created.append(str(steamid))
    except Exception:
        remove_steam_aliases(store, created)
        raise
    return created


def remove_steam_aliases(store, aliases: list[str]) -> None:
    for alias in aliases:
        try:
            store._api("DELETE", "player_aliases", params={"alias": f"eq.{alias}"})
        except Exception:  # noqa: BLE001 - desfazer é melhor esforço
            pass


def find_imported(store, sha: str) -> str | None:
    rows = store._api("GET", "matches", params={"notes": f"ilike.*sha256:{sha}*", "select": "id"})
    return rows[0]["id"] if rows else None


def write_plan(store, plan: dict, bind: dict[str, str] | None = None) -> dict:
    """Grava partidas, estatísticas e detalhes, e registra o confronto. Desfaz tudo se algo falhar.

    ``bind``: {player_id: steamid} para jogadores que ainda não tinham SteamID cadastrado.
    """
    created = [m["id"] for m in plan["matches"]]
    done: list[str] = []
    try:
        for player_id, steamid in (bind or {}).items():
            store._api("PATCH", "players", params={"id": f"eq.{player_id}", "steamid": "is.null"},
                       payload={"steamid": steamid})
        store._api("POST", "matches", params={"on_conflict": "id"}, payload=plan["matches"])
        done.append("matches")
        for table, key, conflict in (("player_stats", "player_stats", "match_id,player_id"),
                                     ("player_match_detail", "details", "match_id,player_id"),
                                     ("player_scope_stats", "scope", "match_id,player_id")):
            store._api("POST", table, params={"on_conflict": conflict}, payload=plan[key])
            done.append(table)
        return store._api("POST", "rpc/register_edb_confronto", payload={"p_bundle": plan["bundle"]})
    except Exception:
        ids = "in.(" + ",".join(created) + ")"
        for table in reversed(done):
            try:
                store._api("DELETE", table, params={"id" if table == "matches" else "match_id": ids})
            except Exception:  # noqa: BLE001 - desfazer é melhor esforço; o erro original segue
                pass
        raise
