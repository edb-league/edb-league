"""Importação de série (md1 / md3) pelo painel, com a mesma regra do ``scripts/edb_import.py``.

Duas etapas, sem estado no servidor: a prévia lê os arquivos e devolve o que foi entendido junto com um ``payload``
(as análises, compactadas); a gravação recebe o ``payload`` de volta, mais as escolhas de identidade, e refaz todas as
conferências antes de escrever.

Cada arquivo pode ser a demo (``.dem``, ``.dem.gz``, ``.gz``) ou a análise que o importador local gera
(``.edb.json``). A demo tem ~230 MB e a análise leva minutos, então o caminho recomendado é analisar no computador.
"""
from __future__ import annotations

import base64
import json
import zlib
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from uuid import uuid4

from edb import demo_pipeline as dp
from edb.demo_importer import prepare_upload
from edb.demo_stats import COUNT_FIELDS, PARSER_VERSION
from edb.hltv_stats import rating2

from . import settings
from .service import LeagueService
from .views import Conflict

MAX_ANALYSIS_BYTES = 2 * 1024 * 1024
MAX_PAYLOAD_BYTES = 8 * 1024 * 1024
MAX_FILES = 8
ANALYSIS_KIND = "edb-analise"
PLAYER_KEYS = ("steamid", "kills", "deaths", "assists", "damage", "rounds", "headshots", "plants", "defuses",
               "kast", "open_kills", "trade_kills", "team")


# --------------------------------------------------------------------------- leitura dos arquivos
class _Upload:
    """Adapta UploadFile ao objeto simples esperado por prepare_upload."""

    def __init__(self, upload):
        self.name = upload.filename or ""
        self._file = upload.file

    def __getattr__(self, item):
        return getattr(self._file, item)


def analysis_problem(analysis) -> str | None:
    """Confere o formato da análise (vinda de um arquivo ou de volta do navegador) antes de usá-la."""
    if not isinstance(analysis, dict):
        return "análise em formato inválido"
    try:
        score = analysis["score"]
        int(score["team_t_first"]), int(score["team_ct_first"]), int(analysis["rounds"])
        rosters = analysis["rosters"]
        list(rosters["team_t_first"]), list(rosters["team_ct_first"])
        players = analysis["players"]
        str(analysis["map"])
        if not isinstance(players, list) or not players:
            return "análise sem jogadores"
        for p in players:
            missing = [k for k in (*PLAYER_KEYS, *COUNT_FIELDS) if k not in p]
            if missing:
                return f"análise de uma versão antiga do leitor (faltam: {', '.join(missing[:3])}...)"
    except (KeyError, TypeError, ValueError):
        return "análise incompleta"
    return None


def already_imported(matches: list[dict], sha: str) -> str | None:
    """Id da partida que já guarda esta demo (o hash fica nas notas; no painel de uma demo só, é o próprio id)."""
    tag = "sha256:" + sha
    for match in matches:
        if str(match.get("id")) == sha or tag in str(match.get("notes") or ""):
            return str(match["id"])
    return None


def _read_json(upload, today: date) -> dp.DemoRun:
    blob = upload.file.read(MAX_ANALYSIS_BYTES + 1)
    if len(blob) > MAX_ANALYSIS_BYTES:
        raise ValueError("arquivo de análise grande demais (limite de 2 MB).")
    try:
        data = json.loads(blob)
    except ValueError:
        raise ValueError("não é um arquivo de análise válido (JSON ilegível).") from None
    if not isinstance(data, dict) or data.get("kind") != ANALYSIS_KIND:
        raise ValueError("este JSON não foi gerado pelo importador da liga (use --painel no scripts/edb_import.py).")
    sha = str(data.get("sha") or "")
    if len(sha) != 64 or not all(c in "0123456789abcdef" for c in sha):
        raise ValueError("a análise não traz o hash da demo.")
    problem = analysis_problem(data.get("analysis"))
    if problem:
        raise ValueError(problem + ". Gere o arquivo de novo com o importador atual.")
    meta = dp.parse_filename(Path(str(data.get("file") or "")), today)
    return dp.DemoRun(meta, sha, data["analysis"])


def _read_demo(upload, today: date) -> dp.DemoRun:
    from edb.demo_stats import analyze

    meta = dp.parse_filename(Path(upload.filename or ""), today)
    folder = None
    try:
        folder, path, sha = prepare_upload(_Upload(upload))
        analysis = analyze(path)
    finally:
        if folder:
            folder.cleanup()
    return dp.DemoRun(meta, sha, analysis)


def read_runs(uploads, matches: list[dict], today: date) -> tuple[list[dp.DemoRun], list[str]]:
    """Lê os arquivos enviados. O que não der para ler vira aviso; o resto segue."""
    if not uploads:
        raise ValueError("Envie os arquivos da série (as demos ou as análises .edb.json).")
    if len(uploads) > MAX_FILES:
        raise ValueError(f"Envie no máximo {MAX_FILES} arquivos por vez.")
    runs: list[dp.DemoRun] = []
    notes: list[str] = []
    for upload in uploads:
        name = upload.filename or "arquivo"
        try:
            run = _read_json(upload, today) if name.lower().endswith(".json") else _read_demo(upload, today)
        except Exception as exc:  # noqa: BLE001 - um arquivo ruim não derruba os outros
            notes.append(f"{name}: {exc}")
            continue
        done = already_imported(matches, run.sha)
        if done:
            notes.append(f"{name}: já importada ({done}).")
            continue
        if any(other.sha == run.sha for other in runs):
            notes.append(f"{name}: arquivo repetido nesta leva.")
            continue
        run.errors, run.warnings = dp.check_demo(run.file, run.analysis)
        runs.append(run)
    return runs, notes


# --------------------------------------------------------------------------- payload entre prévia e gravação
def pack(runs: list[dp.DemoRun]) -> str:
    raw = json.dumps([{"file": r.file.path.name, "sha": r.sha, "analysis": r.analysis} for r in runs],
                     separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(zlib.compress(raw, 9)).decode("ascii")


def unpack(payload: str, today: date) -> list[dp.DemoRun]:
    if len(payload) > MAX_PAYLOAD_BYTES:
        raise ValueError("Os dados da prévia são grandes demais. Leia os arquivos de novo.")
    try:
        decoder = zlib.decompressobj()
        raw = decoder.decompress(base64.urlsafe_b64decode(payload.encode("ascii")), MAX_PAYLOAD_BYTES * 4)
        items = json.loads(raw)
        assert isinstance(items, list) and items
    except Exception:  # noqa: BLE001 - qualquer defeito significa payload inválido
        raise ValueError("Os dados da prévia estão corrompidos. Leia os arquivos de novo.") from None
    runs = []
    for item in items:
        problem = analysis_problem(item.get("analysis") if isinstance(item, dict) else None)
        if problem or not isinstance(item.get("sha"), str):
            raise ValueError("Os dados da prévia estão inválidos" + (f" ({problem})" if problem else "") + ".")
        meta = dp.parse_filename(Path(str(item.get("file") or "")), today)
        run = dp.DemoRun(meta, item["sha"], item["analysis"])
        run.errors, run.warnings = dp.check_demo(meta, item["analysis"])
        runs.append(run)
    return runs


# --------------------------------------------------------------------------- avaliação de uma série
@dataclass
class Evaluated:
    series: dp.Series
    problems: list[str]
    anchors: dict[str, set[str]]
    a_sets: list[set[str]] = field(default_factory=list)
    scores: list[tuple[int, int]] = field(default_factory=list)
    basis: str = ""
    season: dict | None = None
    existing: list[str] = field(default_factory=list)


def _anchors(series: dp.Series, directory: dp.Directory, pt: list[str], pl: list[str]) -> dict[str, set[str]]:
    return {"PT": dp.anchor_steamids(pt, series, directory), "PL": dp.anchor_steamids(pl, series, directory)}


def evaluate(store, series: dp.Series, directory: dp.Directory, swap: bool,
             pt: list[str] | None = None, pl: list[str] | None = None) -> Evaluated:
    problems = list(series.problems) + [e for d in series.demos for e in d.errors]
    anchors = _anchors(series, directory, pt or dp.DEFAULT_ANCHORS["PT"], pl or dp.DEFAULT_ANCHORS["PL"])
    ev = Evaluated(series, problems, anchors)
    try:
        ev.a_sets, ev.scores, ev.basis = dp.assign_teams(series, swap, anchors)
        result_problem = dp.series_result_problem(series, ev.scores)
        if result_problem:
            problems.append(result_problem)
    except ValueError as exc:
        problems.append(str(exc))
    try:
        ev.season = dp.season_for(store._list("league_seasons"), series.played_on)
    except ValueError as exc:
        problems.append(str(exc))
    return ev


def _suggestions(directory: dp.Directory, series: dp.Series) -> tuple[dict[str, str], list[dict]]:
    """({steamid: player_id} já conhecidos, pendências com sugestão por nick igual)."""
    nicks = dp.demo_nicks(series)
    ids: dict[str, str] = {}
    pending = []
    for steam, nick in nicks.items():
        pid = directory.resolve(steam)
        if pid:
            ids[steam] = pid
    taken = set(ids.values())
    for steam, nick in nicks.items():
        if steam in ids:
            continue
        suggestion = directory.suggest(nick)
        if suggestion in taken:
            suggestion = None
        pending.append({"steamid": steam, "nick": nick,
                        "suggestion": {"id": suggestion, "nickname": directory.name(suggestion)} if suggestion else None})
    return ids, pending


def _team_label(steam: str, a_set: set[str]) -> str:
    return "A" if steam in a_set else "B"


def _map_view(run: dp.DemoRun, a_set: set[str], score: tuple[int, int], ids: dict[str, str],
              directory: dp.Directory) -> dict:
    players = []
    for p in sorted(run.analysis["players"], key=lambda x: -int(x["kills"])):
        steam = str(p["steamid"])
        est = rating2({f: p.get(f, 0) for f in COUNT_FIELDS})
        rounds = int(p["rounds"]) or 1
        pid = ids.get(steam)
        players.append({
            "steamid": steam, "nick": str(p.get("nick") or "") or steam, "team": _team_label(steam, a_set),
            "player_id": pid, "player": directory.name(pid) if pid else None,
            "kills": int(p["kills"]), "deaths": int(p["deaths"]), "assists": int(p["assists"]),
            "adr": round(int(p["damage"]) / rounds, 1), "kast": int(p["kast"]),
            "headshots": int(p["headshots"]), "rating": round(est, 2) if est is not None else None,
        })
    return {
        "file": run.file.path.name, "map": str(run.analysis["map"]).title(), "order": run.file.order,
        "rounds": int(run.analysis["rounds"]), "score_a": score[0], "score_b": score[1],
        "warnings": list(run.warnings), "players": players,
    }


def _changes(ev: Evaluated, directory: dp.Directory, ids: dict[str, str], names: tuple[str, str]) -> list[str]:
    nicks = dp.demo_nicks(ev.series)

    def who(steam: str) -> str:
        pid = ids.get(steam)
        return directory.name(pid) if pid else (nicks.get(steam) or steam)

    out = []
    for index, label, came, left in dp.roster_changes(ev.series, ev.a_sets):
        parts = []
        if came:
            parts.append("entrou " + ", ".join(who(x) for x in sorted(came)))
        if left:
            parts.append("saiu " + ", ".join(who(x) for x in sorted(left)))
        team = names[0] if label == "A" else names[1]
        out.append(f"Substituição no mapa {index + 1} ({ev.series.demos[index].file.map}), {team}: {'; '.join(parts)}")
    return out


def preview(service: LeagueService, uploads, names: tuple[str, str], swap: bool) -> dict:
    store = _online_store(service)
    runs, notes = read_runs(uploads, store.matches(), settings.today())
    directory = dp.Directory(store.players(), store._list("player_aliases"))
    series_views = []
    known_stats = store.stats() if runs else []
    known_matches = store.matches() if runs else []
    for series in dp.group_series(runs):
        ev = evaluate(store, series, directory, swap)
        ids, pending = _suggestions(directory, series)
        problems = list(ev.problems)
        if not problems and not pending:
            already = dp.find_existing_series(series, ids, known_matches, known_stats)
            if already:
                problems.append("Esta série já está no banco (" + ", ".join(already) + "). Não será gravada de novo.")
        series_runs = series.demos
        series_views.append({
            "key": f"{series.fmt}-{series.played_on.isoformat()}-{series_runs[0].sha[:8]}",
            "label": series.label, "format": series.fmt, "played_on": series.played_on.isoformat(),
            "season": int(ev.season["number"]) if ev.season else None,
            "basis": ev.basis, "problems": problems, "notes": list(series.notes),
            "changes": _changes(ev, directory, ids, names) if ev.a_sets else [],
            "maps": [_map_view(run, a_set, score, ids, directory)
                     for run, a_set, score in zip(series_runs, ev.a_sets, ev.scores)] if ev.a_sets else [],
            "unresolved": pending, "can_commit": not problems,
            "payload": pack(series_runs),
        })
    return {
        "team_a": names[0], "team_b": names[1], "notes": notes, "series": series_views,
        "players": [{"id": str(p["id"]), "nickname": str(p["nickname"]), "has_steamid": bool(p.get("steamid"))}
                    for p in sorted(directory.players.values(), key=lambda p: str(p["nickname"]).casefold())],
    }


# --------------------------------------------------------------------------- gravação
def _online_store(service: LeagueService):
    store = service.store
    if not getattr(store, "cloud", False):
        raise ValueError("A importação de série precisa do banco online (Supabase).")
    return store


def resolve_choices(directory: dp.Directory, series: dp.Series, choices: dict) -> tuple[dict, dict, dict, dict]:
    """(ids, vínculos {jogador: steamid}, novos {id: nick}, segundas contas {steamid: jogador}) ou ValueError."""
    ids, pending = _suggestions(directory, series)
    bind: dict[str, str] = {}
    new_players: dict[str, str] = {}
    extra: dict[str, str] = {}
    used_nicks = {str(p["nickname"]).casefold() for p in directory.players.values()}
    for item in pending:
        steam, nick = item["steamid"], item["nick"]
        choice = (choices or {}).get(steam)
        label = f"{nick or steam} (SteamID {steam})"
        if not isinstance(choice, dict) or not choice.get("kind"):
            raise ValueError(f"Diga quem é {label}: vincule a um jogador, marque como outra conta ou crie um novo.")
        kind = choice["kind"]
        if kind == "new":
            name = str(choice.get("nickname") or "").strip()
            if not name:
                raise ValueError(f"Informe o nickname do novo jogador para {label}.")
            if name.casefold() in used_nicks:
                raise ValueError(f"Já existe um jogador chamado {name}. Vincule {label} a ele.")
            pid = str(uuid4())
            used_nicks.add(name.casefold())
            new_players[pid] = name
            ids[steam], bind[pid] = pid, steam
            continue
        pid = str(choice.get("player_id") or "")
        player = directory.players.get(pid)
        if player is None:
            raise ValueError(f"Jogador escolhido para {label} não foi encontrado.")
        if pid in ids.values() or pid in bind or pid in extra.values():
            raise ValueError(f"{directory.name(pid)} já está nesta série com outra conta.")
        if kind == "link":
            if player.get("steamid"):
                raise ValueError(f"{directory.name(pid)} já tem SteamID cadastrado; use \"outra conta\" para {label}.")
            ids[steam], bind[pid] = pid, steam
        elif kind == "alias":
            if not player.get("steamid"):
                raise ValueError(f"{directory.name(pid)} ainda não tem SteamID; vincule {label} diretamente a ele.")
            ids[steam] = pid
            extra[steam] = pid
        else:
            raise ValueError(f"Escolha desconhecida para {label}.")
    return ids, bind, new_players, extra


def commit(service: LeagueService, body: dict) -> dict:
    store = _online_store(service)
    runs = unpack(str(body.get("payload") or ""), settings.today())
    known_matches = store.matches()
    for run in runs:
        done = already_imported(known_matches, run.sha)
        if done:
            raise Conflict(f"{run.file.path.name} já foi importada ({done}).")
    names = (str(body.get("team_a") or "PT").strip() or "PT", str(body.get("team_b") or "PL").strip() or "PL")
    swap = bool(body.get("swap"))
    directory = dp.Directory(store.players(), store._list("player_aliases"))
    groups = dp.group_series(runs)
    if len(groups) != 1:
        raise ValueError("Grave uma série por vez: estes arquivos formam mais de uma.")
    series = groups[0]
    ev = evaluate(store, series, directory, swap)
    if ev.problems:
        raise ValueError("A série não pode ser gravada: " + " ".join(ev.problems))
    ids, bind, new_players, extra = resolve_choices(directory, series, body.get("choices") or {})
    duplicated = dp.duplicate_players(series, ids)
    if duplicated:
        raise ValueError(" ".join(duplicated) + " Uma segunda conta não pode jogar junto com a principal.")
    known_stats = store.stats()
    already = dp.find_existing_series(series, ids, known_matches, known_stats)
    if already:
        raise Conflict("Esta série (ou parte dela) já está no banco: " + ", ".join(already)
                       + ". Para completar uma partida antiga com os dados da demo, use o importador local.")
    taken = {str(m["id"]) for m in known_matches}
    match_ids = dp.next_match_ids(series, ev.season, store._list("bo3_series"), taken)
    plan = dp.build_plan(series, ev.season, match_ids, ids, names[0], names[1], swap, ev.anchors)

    created_players: list[str] = []
    created_aliases: list[str] = []
    try:
        created_aliases = dp.write_steam_aliases(store, extra)
        for pid, nickname in new_players.items():
            store.save_player(nickname, stars=3, steamid=bind[pid], player_id=pid)
            created_players.append(pid)
        dp.write_plan(store, plan, {p: s for p, s in bind.items() if p not in new_players})
    except Exception as exc:
        for pid in created_players:
            try:
                store._api("DELETE", "season_player_stars", params={"player_id": f"eq.{pid}"})
                store._api("DELETE", "players", params={"id": f"eq.{pid}"})
            except Exception:  # noqa: BLE001 - desfazer é melhor esforço; o erro original segue
                pass
        dp.remove_steam_aliases(store, created_aliases)
        text = str(exc)
        hint = (" O banco ainda não aceita substituições: falta aplicar db/migrations/20261021_confronto_com_substituicoes.sql."
                if "exatamente cinco" in text or "mesmo elenco" in text else "")
        raise RuntimeError("Não foi possível gravar a série; nada ficou salvo." + hint) from exc
    service.invalidate()
    return {"ok": True, "match_ids": match_ids, "label": series.label, "parser_version": PARSER_VERSION}
