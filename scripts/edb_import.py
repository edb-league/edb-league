"""Importador de demos CS2 da EDB LEAGUE.

Lê a pasta de demos, processa no próprio computador e envia só o resultado ao Supabase.
Sem --gravar nada é escrito no banco (apenas prévia).

Exemplos (PowerShell, na raiz do repositório):
    python scripts/edb_import.py                      # prévia de tudo que está na pasta
    python scripts/edb_import.py --gravar             # pergunta antes de gravar cada série
    python scripts/edb_import.py --gravar --sim       # grava as séries sem pendência, sem perguntar
    python scripts/edb_import.py --vigiar --gravar --sim   # fica de olho na pasta
    python scripts/edb_import.py --painel             # lê as demos e gera os arquivos .edb.json para enviar pelo painel

Credenciais: variáveis SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY, ou um arquivo .env
na raiz do repositório (já ignorado pelo git). Nunca coloque a chave em outro lugar.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "edb"))

from edb import demo_pipeline as dp  # noqa: E402

DEFAULT_FOLDER = r"C:\Users\Usuario\Documents\Demos EDB"
SETTLE_SECONDS = 20  # arquivo mexido há menos que isso ainda pode estar sendo copiado


def load_env() -> None:
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def open_store():
    url, key = os.environ.get("SUPABASE_URL", ""), os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not (url and key):
        return None
    from edb.storage import Store
    return Store(url, key)


def ask(question: str, default: str = "") -> str:
    try:
        return input(question).strip() or default
    except EOFError:
        return default


# --------------------------------------------------------------------------- prévia
def adr(p: dict) -> float:
    return p["damage"] / p["rounds"] if p["rounds"] else 0.0


def print_series(series: dp.Series, directory: dp.Directory | None, a_sets: list[set[str]], names: tuple[str, str],
                 scores: list[tuple[int, int]], basis: str = "") -> None:
    print(f"\n=== {series.label} ===")
    if basis:
        print(f"  {names[0]} = {basis}")
    for note in series.notes:
        print(f"  AVISO: {note}")

    def who_is(steam: str, nick: str = "") -> str:
        pid = directory.resolve(steam) if directory else None
        return directory.name(pid) if pid else f"{nick or steam} (SteamID {steam})"

    nicks = dp.demo_nicks(series)
    for index, label, came, left in dp.roster_changes(series, a_sets):
        team = names[0] if label == "A" else names[1]
        parts = []
        if came:
            parts.append("entrou " + ", ".join(who_is(x, nicks.get(x, "")) for x in sorted(came)))
        if left:
            parts.append("saiu " + ", ".join(who_is(x, nicks.get(x, "")) for x in sorted(left)))
        print(f"  Substituição no mapa {index + 1} ({series.demos[index].file.map}), {team}: {'; '.join(parts)}")
    for run, (a, b), team_a in zip(series.demos, scores, a_sets):
        print(f"\n  {run.file.path.name}  |  {run.analysis['map']}  |  {names[0]} {a} x {b} {names[1]}"
              f"  |  {run.analysis['rounds']} rounds")
        for label, in_a in ((names[0], True), (names[1], False)):
            print(f"    {label}")
            rows = [p for p in run.analysis["players"] if (str(p["steamid"]) in team_a) == in_a]
            for p in sorted(rows, key=lambda x: -x["kills"]):
                print(f"      {who_is(str(p['steamid']), str(p['nick'])):<34} {p['kills']:>2}/{p['deaths']:>2}/{p['assists']:>2}  "
                      f"ADR {adr(p):5.1f}  KAST {p['kast']:>3}%  HS {p['headshots']:>2}")
        for w in run.warnings:
            print(f"    AVISO: {w}")


def resolve_identities(series: dp.Series, directory: dp.Directory, interactive: bool):
    """Devolve (ids, bind, novos, extra) ou None se alguma identidade ficou sem resolver.

    ``extra``: {steamid: player_id} para segundas contas de jogadores já cadastrados.
    """
    ids: dict[str, str] = {}
    bind: dict[str, str] = {}
    new_players: dict[str, str] = {}   # player_id -> nick
    extra: dict[str, str] = {}         # steamid -> player_id (segunda conta)
    nicks = dp.demo_nicks(series)
    unresolved = []
    for steam, nick in nicks.items():
        pid = directory.resolve(steam)
        if pid:
            ids[steam] = pid
        else:
            unresolved.append((steam, nick))
    free = [p for p in directory.players.values()
            if not p.get("steamid") and str(p["id"]) not in bind.values() and str(p["id"]) not in ids.values()]
    for steam, nick in unresolved:
        suggestion = directory.suggest(nick)
        if suggestion and suggestion in ids.values():
            suggestion = None
        if suggestion and not interactive:
            ids[steam], bind[suggestion] = suggestion, steam
            print(f"  Vinculado automaticamente: '{nick}' -> {directory.name(suggestion)} (nick igual, sem SteamID).")
            continue
        if not interactive:
            print(f"  PENDENTE: SteamID {steam} ('{nick}') não está cadastrado. Rode sem --sim para vincular.")
            return None
        print(f"\n  SteamID {steam} ('{nick}') não está cadastrado.")
        candidates = [p for p in free if str(p["id"]) not in ids.values()]
        if suggestion:
            if ask(f"  Vincular a {directory.name(suggestion)}? [s/N] ").lower().startswith("s"):
                ids[steam], bind[suggestion] = suggestion, steam
                continue
        for i, p in enumerate(candidates, 1):
            print(f"    {i}) {p['nickname']}")
        choice = ask("  Número do jogador, 'n' para criar novo, 'o' para outra conta de jogador já cadastrado, "
                     "Enter para pular esta série: ")
        if choice.lower() == "o":
            taken_ids = set(ids.values())
            registered = [p for p in directory.players.values() if str(p["id"]) not in taken_ids]
            wanted = ask("  Nick do jogador já cadastrado: ").strip().casefold()
            found = [p for p in registered if str(p["nickname"]).casefold() == wanted]
            if len(found) != 1:
                print("  Jogador não encontrado (ou já está na série com outra conta).")
                return None
            pid = str(found[0]["id"])
            ids[steam] = pid
            extra[steam] = pid
        elif choice.lower() == "n":
            nickname = ask(f"  Nick do novo jogador [{nick}]: ", nick)
            pid = str(uuid4())
            new_players[pid] = nickname
            ids[steam], bind[pid] = pid, steam
        elif choice.isdigit() and 1 <= int(choice) <= len(candidates):
            pid = str(candidates[int(choice) - 1]["id"])
            ids[steam], bind[pid] = pid, steam
        else:
            return None
    return ids, bind, new_players, extra


# --------------------------------------------------------------------------- execução
def collect(folder: Path, store, only: list[str] | None) -> tuple[list[dp.DemoRun], list[str]]:
    notes: list[str] = []
    runs: list[dp.DemoRun] = []
    everything = sorted(p for p in folder.iterdir() if p.is_file() and not p.name.startswith("."))
    files = [p for p in everything if p.name.lower().endswith((".dem", ".dem.gz", ".gz"))]
    for p in everything:
        if p not in files:
            notes.append(f"{p.name}: ignorado (a extensão deve ser .dem, .dem.gz ou .gz).")
    if not everything:
        notes.append(f"A pasta {folder} está vazia.")
    if only:
        wanted = {o.lower() for o in only}
        files = [p for p in files if p.name.lower() in wanted]
    for path in files:
        if time.time() - path.stat().st_mtime < SETTLE_SECONDS:
            notes.append(f"{path.name}: ainda sendo copiado; fica para a próxima rodada.")
            continue
        try:
            meta = dp.parse_filename(path)
        except ValueError as exc:
            notes.append(str(exc))
            continue
        sha = dp.sha256_file(path)
        if store is not None:
            done = dp.find_imported(store, sha)
            if done:
                notes.append(f"{path.name}: já importada ({done}).")
                continue
        print(f"Lendo {path.name} ...", flush=True)
        try:
            sha, analysis = dp.analyze_file(path, folder / ".edb_cache")
        except Exception as exc:  # noqa: BLE001 - mostrar e seguir com os outros arquivos
            notes.append(f"{path.name}: não foi possível ler a demo ({exc}).")
            continue
        run = dp.DemoRun(meta, sha, analysis)
        run.errors, run.warnings = dp.check_demo(meta, analysis)
        runs.append(run)
    return runs, notes


def export_for_panel(runs: list[dp.DemoRun], folder: Path) -> None:
    """Grava a análise de cada demo em <pasta>/para_o_painel/<nome>.edb.json (poucos KB; a demo tem ~230 MB)."""
    out = folder / "para_o_painel"
    out.mkdir(exist_ok=True)
    for run in runs:
        target = out / (dp._stem(run.file.path.name) + ".edb.json")
        target.write_text(json.dumps({"kind": "edb-analise", "file": run.file.path.name, "sha": run.sha,
                                      "analysis": run.analysis}), encoding="utf-8")
        print(f"  Gerado: {target}")
    print()
    print(f"{len(runs)} arquivo(s) em {out}. No painel, aba Importar > Série, envie os arquivos da mesma série juntos.")


def run_once(args, store) -> int:
    folder = Path(args.pasta)
    if not folder.is_dir():
        print(f"Pasta não encontrada: {folder}")
        return 2
    runs, notes = collect(folder, store, args.so)
    for n in notes:
        print(f"- {n}")
    if not runs:
        print("Nada novo para importar.")
        return 0
    if args.painel:
        export_for_panel(runs, folder)
        return 0
    directory = seasons = existing = taken = None
    if store is not None:
        directory = dp.Directory(store.players(), store._list("player_aliases"))
        seasons = store._list("league_seasons")
        existing = store._list("bo3_series")
        taken = {str(m["id"]) for m in store.matches()}
    reserved: dict[tuple[int, str], int] = {}
    written = 0
    for series in dp.group_series(runs):
        problems = list(series.problems) + [e for d in series.demos for e in d.errors]
        anchors = {"PT": dp.anchor_steamids(args.ancora_pt, series, directory),
                   "PL": dp.anchor_steamids(args.ancora_pl, series, directory)}
        try:
            a_sets, scores, basis = dp.assign_teams(series, args.trocar_times, anchors)
            result_problem = dp.series_result_problem(series, scores)
            if result_problem:
                problems.append(result_problem)
        except ValueError as exc:
            problems.append(str(exc))
            a_sets, scores, basis = [], [], ""
        if problems:
            print(f"\n=== {series.label} ===")
            for p in problems:
                print(f"  NÃO IMPORTÁVEL: {p}")
            continue
        names = (args.time_a, args.time_b)
        print_series(series, directory, a_sets, names, scores, basis)
        if not args.gravar:
            continue
        if store is None:
            print("\n  Sem SUPABASE_URL/SUPABASE_SERVICE_ROLE_KEY: só prévia.")
            continue
        try:
            season = dp.season_for(seasons, series.played_on)
        except ValueError as exc:
            print(f"\n  NÃO GRAVADO: {exc}")
            continue
        resolved = resolve_identities(series, directory, interactive=not args.sim)
        if resolved is None:
            print("  Série não gravada (identidades pendentes).")
            continue
        ids, bind, new_players, extra = resolved
        duplicated = dp.duplicate_players(series, ids)
        if duplicated:
            for line in duplicated:
                print(f"  NÃO GRAVADO: {line}")
            print("  Uma segunda conta não pode jogar junto com a conta principal. Confira os vínculos em "
                  "player_aliases e os SteamIDs dos jogadores.")
            continue
        known_matches, known_stats = store.matches(), store.stats()
        already = dp.find_existing_series(series, ids, known_matches, known_stats)
        if already:
            existing_map = dp.existing_by_demo(series, ids, known_matches, known_stats)
            if len(existing_map) != len(series.demos):
                print(f"  JÁ EXISTE no banco só parte desta série ({', '.join(already)}). Não gravada, para não duplicar.")
                continue
            have = {str(d["match_id"]) for d in store.match_details()}
            completion = dp.completion_plan(series, ids, existing_map, known_matches, have)
            if not completion["match_ids"]:
                print(f"  JÁ EXISTE no banco, com os dados da demo: {', '.join(already)}. Nada a fazer.")
                continue
            print(f"  JÁ EXISTE no banco sem os dados da demo: {', '.join(completion['match_ids'])}.")
            print("  Posso gravar só os detalhes da demo nessas partidas (placar, times e série não mudam).")
            if not args.sim and not ask("  Gravar só os detalhes? [s/N] ").lower().startswith("s"):
                print("  Pulada.")
                continue
            aliases_done: list[str] = []
            try:
                aliases_done = dp.write_steam_aliases(store, extra)
                dp.write_completion(store, completion, {str(m["id"]): str(m.get("notes") or "") for m in known_matches})
            except Exception as exc:  # noqa: BLE001
                dp.remove_steam_aliases(store, aliases_done)
                print(f"  FALHOU e foi desfeito: {exc}")
                continue
            for steam, pid in extra.items():
                directory.by_steam[steam] = pid
            written += 1
            print(f"  Detalhes gravados: {', '.join(completion['match_ids'])}")
            continue
        if not args.sim:
            if not ask(f"\n  Gravar {series.label} na temporada {season['number']}? [s/N] ").lower().startswith("s"):
                print("  Pulada.")
                continue
        key = (int(season["number"]), series.fmt)
        match_ids = dp.next_match_ids(series, season, existing, taken, reserved.get(key, 0))
        plan = dp.build_plan(series, season, match_ids, ids, args.time_a, args.time_b, args.trocar_times, anchors)
        created: list[str] = []
        created_aliases: list[str] = []
        try:
            created_aliases = dp.write_steam_aliases(store, extra)
            for pid, nickname in new_players.items():
                store.save_player(nickname, stars=3, steamid=bind[pid], player_id=pid)
                created.append(pid)
            bind_existing = {p: s for p, s in bind.items() if p not in new_players}
            dp.write_plan(store, plan, bind_existing)
        except Exception as exc:  # noqa: BLE001
            for pid in created:
                try:
                    # o gatilho de estrelas cria uma linha por jogador novo; sem apagá-la o jogador não sai
                    store._api("DELETE", "season_player_stars", params={"player_id": f"eq.{pid}"})
                    store._api("DELETE", "players", params={"id": f"eq.{pid}"})
                except Exception as undo_exc:  # noqa: BLE001
                    print(f"  AVISO: não consegui remover o jogador novo {new_players.get(pid, pid)}: {undo_exc}")
            dp.remove_steam_aliases(store, created_aliases)
            print(f"  FALHOU e foi desfeito: {exc}")
            if "exatamente cinco" in str(exc) or "mesmo elenco" in str(exc):
                print("  Esta série tem jogadores que entraram ou saíram. O banco ainda não aceita isso: "
                      "falta aplicar a migração db/migrations/20261021_confronto_com_substituicoes.sql.")
            continue
        for steam, pid in extra.items():
            directory.by_steam[steam] = pid
        reserved[key] = reserved.get(key, 0) + 1
        taken.update(match_ids)
        written += 1
        print(f"  Gravado: {', '.join(match_ids)}")
    if args.gravar:
        print(f"\n{written} série(s) gravada(s).")
    else:
        print("\nPrévia apenas. Use --gravar para enviar ao banco.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Importa demos CS2 da pasta para a EDB LEAGUE.")
    parser.add_argument("--pasta", default=os.environ.get("EDB_DEMOS_DIR", DEFAULT_FOLDER))
    parser.add_argument("--gravar", action="store_true", help="envia ao Supabase (sem isso, só prévia)")
    parser.add_argument("--sim", action="store_true", help="não pergunta; grava só séries sem pendência")
    parser.add_argument("--painel", action="store_true",
                        help="só lê as demos e gera os arquivos .edb.json para enviar pelo painel (não grava no banco)")
    parser.add_argument("--vigiar", action="store_true", help="repete a leitura da pasta a cada --intervalo segundos")
    parser.add_argument("--intervalo", type=int, default=60)
    parser.add_argument("--trocar-times", action="store_true", help="inverte PT e PL depois de aplicar as âncoras")
    parser.add_argument("--ancora-pt", nargs="+", default=dp.DEFAULT_ANCHORS["PT"],
                        help="jogador(es) que definem PT (nick na demo, nick/alias do banco ou SteamID)")
    parser.add_argument("--ancora-pl", nargs="+", default=dp.DEFAULT_ANCHORS["PL"],
                        help="jogador(es) que definem PL")
    parser.add_argument("--time-a", default="PT")
    parser.add_argument("--time-b", default="PL")
    parser.add_argument("--so", nargs="*", help="processa apenas estes arquivos")
    args = parser.parse_args()
    load_env()
    store = open_store()
    if store is None:
        print("Aviso: SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY não configurados; não dá para conferir "
              "duplicatas nem identificar jogadores.\n")
    if not args.vigiar:
        return run_once(args, store)
    print(f"Vigiando {args.pasta} a cada {args.intervalo}s. Ctrl+C para parar.")
    try:
        while True:
            run_once(args, store)
            time.sleep(args.intervalo)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())
