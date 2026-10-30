from datetime import date
from pathlib import Path

import pytest

from edb import demo_pipeline as dp
from edb.demo_stats import COUNT_FIELDS, PARSER_VERSION

TODAY = date(2026, 10, 20)


def name(n):
    return dp.parse_filename(Path(n), TODAY)


def test_nome_valido_md3_e_md1():
    a = name("md3_inferno_20_10_1.dem")
    assert (a.fmt, a.map, a.played_on, a.order) == ("bo3", "inferno", date(2026, 10, 20), 1)
    b = name("MD1_Mirage_19_10.dem.gz")
    assert (b.fmt, b.map, b.played_on, b.order) == ("bo1", "mirage", date(2026, 10, 19), 1)
    assert name("md1_dust2_01_10_2.dem").order == 2


def test_data_futura_vira_ano_anterior():
    assert name("md1_mirage_25_12.dem").played_on == date(2025, 12, 25)
    assert name("md1_mirage_21_10.dem").played_on == date(2026, 10, 21)  # amanhã ainda é este ano


@pytest.mark.parametrize("bad", [
    "md3_inferno_20_10.dem",          # md3 sem ordem
    "md3_inferno_20_10_4.dem",        # ordem fora de 1..3
    "md2_inferno_20_10_1.dem",        # formato inexistente
    "md3_inferno_31_02_1.dem",        # data impossível
    "md3_pokemon_20_10_1.dem",        # mapa desconhecido
    "md3_inferno_20_10_1.zip",        # extensão
    "partida.dem",
])
def test_nome_invalido(bad):
    with pytest.raises(ValueError):
        name(bad)


def player(steam, nick, **extra):
    row = {f: 0 for f in COUNT_FIELDS}
    row.update(steamid=steam, nick=nick, kills=15, deaths=12, assists=3, damage=1500, rounds=20,
               kast=70, open_kills=2, trade_kills=1, headshots=6, plants=0, defuses=0,
               rounds_t=10, rounds_ct=10, kills_t=7, kills_ct=8, deaths_t=6, deaths_ct=6,
               assists_t=1, assists_ct=2, damage_t=700, damage_ct=800, kast_rounds_t=7, kast_rounds_ct=7,
               he_damage=10, fire_damage=5, flash_seconds=3.5, smokes_thrown=4, enemies_flashed=2,
               weapon_kills={"ak47": 10}, clutches={"1v1": [1, 0]})
    row.update(extra)
    return row


def timeline(t_score, ct_score):
    """Quem começou de T vence os primeiros t_score rounds; o outro time, o resto (só importa o formato)."""
    running, rounds = [0, 0], []
    for n in range(1, t_score + ct_score + 1):
        winner = "t_first" if n <= t_score else "ct_first"
        running[0 if winner == "t_first" else 1] += 1
        rounds.append({"round": n, "winner": winner, "side": "t" if n <= 12 else "ct", "reason": "eliminacao",
                       "planted": n == 2, "score": list(running)})
    return rounds


def analysis(map_name, t_ids, ct_ids, t_score, ct_score):
    players = [player(s, f"n{s}") for s in t_ids + ct_ids]
    return {"parser_version": 1, "map": map_name, "server": "XPLAY.GG", "rounds": t_score + ct_score,
            "overtime": False, "score": {"team_t_first": t_score, "team_ct_first": ct_score},
            "rosters": {"team_t_first": t_ids, "team_ct_first": ct_ids}, "players": players,
            "timeline": timeline(t_score, ct_score)}


A = [str(i) for i in range(1, 6)]
B = [str(i) for i in range(6, 11)]


def run(filename, map_name, t_ids, ct_ids, t_score, ct_score):
    f = name(filename)
    r = dp.DemoRun(f, "sha-" + filename, analysis(map_name, t_ids, ct_ids, t_score, ct_score))
    r.errors, r.warnings = dp.check_demo(f, r.analysis)
    return r


def bo3_runs():
    return [
        run("md3_anubis_20_10_1.dem", "anubis", B, A, 7, 13),     # A começa de CT e vence 13x7
        run("md3_mirage_20_10_2.dem", "mirage", A, B, 7, 13),     # A começa de T e perde 7x13
        run("md3_inferno_20_10_3.dem", "inferno", B, A, 8, 13),   # A de CT, vence 13x8
    ]


def test_confere_mapa_do_nome_com_a_demo():
    r = run("md3_anubis_20_10_1.dem", "mirage", B, A, 7, 13)
    assert any("o nome diz anubis" in e for e in r.errors)


def test_placar_e_jogadores_invalidos():
    r = run("md1_mirage_20_10.dem", "mirage", A, B, 10, 10)
    assert any("empatado" in e for e in r.errors)
    f = name("md1_mirage_20_10.dem")
    errors, _ = dp.check_demo(f, analysis("mirage", A[:4], B, 7, 13))
    assert any("10 SteamIDs" in e for e in errors)


def test_agrupa_md3_por_data_e_elenco():
    series = dp.group_series(bo3_runs())
    assert len(series) == 1 and series[0].complete
    assert [d.file.map for d in series[0].demos] == ["anubis", "mirage", "inferno"]


def test_md3_incompleta_e_md1_separadas():
    # falta o mapa 1 (só as ordens 2 e 3): incompleta no agrupamento
    runs = bo3_runs()[1:] + [run("md1_nuke_20_10.dem", "nuke", A, B, 13, 5)]
    series = {s.fmt: s for s in dp.group_series(runs)}
    assert not series["bo3"].complete and "faltam" in series["bo3"].problems[0]
    assert series["bo1"].complete


def two_maps(score2=(13, 5)):
    return [run("md3_anubis_20_10_1.dem", "anubis", A, B, 13, 7),
            run("md3_mirage_20_10_2.dem", "mirage", A, B, *score2)]


def test_md3_pode_acabar_2x0_com_dois_mapas():
    s = dp.group_series(two_maps())[0]
    assert s.complete
    _, scores, _ = dp.assign_teams(s)
    assert scores == [(13, 7), (13, 5)] and dp.series_result_problem(s, scores) is None


def test_md3_com_dois_mapas_1x1_esta_incompleta():
    s = dp.group_series(two_maps(score2=(5, 13)))[0]
    _, scores, _ = dp.assign_teams(s)
    problem = dp.series_result_problem(s, scores)
    assert problem and "1x1" in problem and "ordem 3" in problem


def test_md3_com_terceiro_mapa_depois_de_2x0_nao_fecha():
    runs = two_maps() + [run("md3_inferno_20_10_3.dem", "inferno", A, B, 13, 9)]
    s = dp.group_series(runs)[0]
    _, scores, _ = dp.assign_teams(s)
    assert "decidida em 2x0 depois do mapa 2" in dp.series_result_problem(s, scores)
    # 2x1 normal continua valendo
    ok = dp.group_series(bo3_runs())[0]
    _, scores, _ = dp.assign_teams(ok)
    assert dp.series_result_problem(ok, scores) is None


def test_plano_de_md3_2x0_tem_dois_mapas():
    s = dp.group_series(two_maps())[0]
    ids = {str(i): f"p{i}" for i in range(1, 11)}
    mids = dp.next_match_ids(s, {"number": 1}, [], set())
    plan = dp.build_plan(s, {"number": 1}, mids, ids, "PT", "PL")
    assert len(mids) == 2 and len(plan["matches"]) == 2 and len(plan["player_stats"]) == 20
    assert plan["bundle"]["format"] == "bo3" and len(plan["bundle"]["matches"]) == 2


def test_times_seguem_o_primeiro_mapa():
    s = dp.group_series(bo3_runs())[0]
    a_sets, scores, _ = dp.assign_teams(s)
    assert a_sets == [set(B), set(B), set(B)]  # B começou de T no primeiro mapa
    assert scores == [(7, 13), (13, 7), (8, 13)]
    a_sets, scores, _ = dp.assign_teams(s, swap=True)
    assert a_sets == [set(A)] * 3 and scores == [(13, 7), (7, 13), (13, 8)]


def test_ancoras_definem_pt_e_pl():
    s = dp.group_series(bo3_runs())[0]
    # "n1" é o nick de A na demo; "n6" é o de B
    anchors = {"PT": dp.anchor_steamids(["n1"], s), "PL": dp.anchor_steamids(["n6"], s)}
    assert anchors == {"PT": {"1"}, "PL": {"6"}}
    a_sets, scores, basis = dp.assign_teams(s, anchors=anchors)
    assert a_sets == [set(A)] * 3 and scores == [(13, 7), (7, 13), (13, 8)] and "âncora de PT" in basis
    # só a âncora de PL na série: PT é o oposto
    a_sets, _, basis = dp.assign_teams(s, anchors={"PT": set(), "PL": {"6"}})
    assert a_sets == [set(A)] * 3 and "oposto" in basis
    # --trocar-times inverte depois das âncoras
    a_sets, _, _ = dp.assign_teams(s, swap=True, anchors=anchors)
    assert a_sets == [set(B)] * 3
    # nenhuma âncora presente: volta à regra antiga
    a_sets, _, basis = dp.assign_teams(s, anchors={"PT": set(), "PL": set()})
    assert a_sets == [set(B)] * 3 and "nenhuma âncora" in basis


def test_ancoras_no_mesmo_time_o_time_e_pt():
    """Regra do João: se Pyetev (Neteb) e Scby jogam juntos, esse time é PT."""
    s = dp.group_series(bo3_runs())[0]
    a_sets, scores, basis = dp.assign_teams(s, anchors={"PT": {"1"}, "PL": {"2"}})
    assert a_sets == [set(A)] * 3 and "juntas" in basis
    assert scores == [(13, 7), (7, 13), (13, 8)]


def test_ancora_por_nick_do_banco_e_por_steamid():
    s = dp.group_series(bo3_runs())[0]
    d = dp.Directory(players_db(), [{"alias": "Neteb", "player_id": "p1"}])
    assert dp.anchor_steamids(["Neteb"], s, d) == {"1"}        # alias do banco -> steamid
    assert dp.anchor_steamids(["Nick7"], s, d) == {"7"}        # nick do banco
    assert dp.anchor_steamids(["9"], s) == {"9"}               # SteamID direto
    assert dp.anchor_steamids(["ninguem"], s, d) == set()


def test_partida_ja_cadastrada_nao_duplica():
    s = dp.group_series(bo3_runs())[0]
    ids = {str(i): f"p{i}" for i in range(1, 11)}
    roster = [f"p{i}" for i in range(1, 11)]
    matches = [{"id": "edb-t1-bo3-01-anubis", "played_at": "2026-10-19", "map_name": "Anubis"},
               {"id": "outro", "played_at": "2026-10-20", "map_name": "Nuke"}]
    stats = [{"match_id": "edb-t1-bo3-01-anubis", "player_id": p} for p in roster]
    assert dp.find_existing_series(s, ids, matches, stats) == ["edb-t1-bo3-01-anubis"]
    matches[0]["played_at"] = "2026-10-10"                      # outra data: é outra partida
    assert dp.find_existing_series(s, ids, matches, stats) == []
    matches[0]["played_at"] = "2026-10-19"
    stats[0]["player_id"] = "p99"                               # outro elenco: é outra partida
    assert dp.find_existing_series(s, ids, matches, stats) == []


def test_substituicao_no_meio_da_serie_e_aceita():
    """Alguém entra e alguém sai entre mapas: continua sendo uma série."""
    runs = bo3_runs()
    runs[1] = run("md3_mirage_20_10_2.dem", "mirage", A[:4] + ["99"], B, 7, 13)
    series = dp.group_series(runs)
    assert len(series) == 1 and series[0].complete
    anchors = {"PT": {"1"}, "PL": {"6"}}
    a_sets, scores, _ = dp.assign_teams(series[0], anchors=anchors)
    assert a_sets[1] == set(A[:4]) | {"99"} and scores == [(13, 7), (7, 13), (13, 8)]
    changes = dp.roster_changes(series[0], a_sets)
    assert (1, "A", {"99"}, {"5"}) in changes and (2, "A", {"5"}, {"99"}) in changes


def test_substituicao_sem_ancora_segue_o_time_do_mapa_anterior():
    runs = bo3_runs()
    runs[1] = run("md3_mirage_20_10_2.dem", "mirage", A[:4] + ["99"], B, 7, 13)
    s = dp.group_series(runs)[0]
    a_sets, _, basis = dp.assign_teams(s, anchors={"PT": set(), "PL": set()})
    assert a_sets[0] == set(B) and a_sets[1] == set(B) and "continuidade" in basis


def test_jogador_nos_dois_times_da_serie_e_erro():
    runs = bo3_runs()
    runs[1] = run("md3_mirage_20_10_2.dem", "mirage", A[:4] + ["6"], B[1:] + ["5"], 7, 13)
    s = dp.group_series(runs)[0]
    with pytest.raises(ValueError, match="nos dois times"):
        dp.assign_teams(s, anchors={"PT": {"1"}, "PL": {"7"}})


def test_elenco_muito_diferente_gera_aviso_e_duas_md3_no_dia_separam_por_elenco():
    runs = bo3_runs()
    runs[1] = run("md3_mirage_20_10_2.dem", "mirage", ["31", "32", "33", "34", "35"], ["36", "37", "38", "39", "40"], 7, 13)
    s = dp.group_series(runs)[0]
    assert any("repetem" in n for n in s.notes)
    # seis arquivos md3 no mesmo dia: são duas séries, separadas pelo elenco
    other = [run("md3_nuke_20_10_1.dem", "nuke", ["21", "22", "23", "24", "25"], ["26", "27", "28", "29", "30"], 13, 5),
             run("md3_ancient_20_10_2.dem", "ancient", ["21", "22", "23", "24", "25"], ["26", "27", "28", "29", "30"], 13, 6),
             run("md3_vertigo_20_10_3.dem", "vertigo", ["21", "22", "23", "24", "25"], ["26", "27", "28", "29", "30"], 6, 13)]
    series = dp.group_series(bo3_runs() + other)
    assert len(series) == 2 and all(x.complete for x in series)


def players_db():
    rows = [{"id": f"p{i}", "nickname": f"Nick{i}", "steamid": str(i)} for i in range(1, 10)]
    rows.append({"id": "p10", "nickname": "VnD", "steamid": None})
    return rows


def test_directory_steamid_automatico_e_nick_so_como_sugestao():
    d = dp.Directory(players_db(), [{"alias": "vnd2", "player_id": "p10"}])
    assert d.resolve("3") == "p3" and d.resolve("77") is None
    assert d.suggest("vnd") == "p10" and d.suggest("vnd2") == "p10"
    assert d.suggest("Nick3") is None  # já tem outro SteamID: nunca sugerir


def test_directory_segunda_conta_por_alias_de_steamid():
    d = dp.Directory(players_db(), [{"alias": "76561199012257243", "player_id": "p3"}])
    assert d.resolve("76561199012257243") == "p3" and d.resolve("3") == "p3"
    # alias comum (nick) não vira SteamID
    d2 = dp.Directory(players_db(), [{"alias": "vnd2", "player_id": "p10"}])
    assert d2.resolve("vnd2") is None
    # o SteamID principal vence se houver conflito
    d3 = dp.Directory(players_db(), [{"alias": "5", "player_id": "p9"}])
    assert d3.resolve("5") == "p5"


class AliasStore:
    def __init__(self, fail_on=None):
        self.calls, self.fail_on = [], fail_on

    def _api(self, method, table, *, params=None, payload=None):
        self.calls.append((method, table, params, payload))
        if self.fail_on and payload and payload.get("alias") == self.fail_on:
            raise RuntimeError("falhou")
        return []


def test_grava_e_desfaz_segundas_contas():
    store = AliasStore()
    done = dp.write_steam_aliases(store, {"76561199012257243": "p3"})
    assert done == ["76561199012257243"]
    assert store.calls[0][:2] == ("POST", "player_aliases")
    assert store.calls[0][3] == {"alias": "76561199012257243", "player_id": "p3"}
    store = AliasStore(fail_on="76561199000000002")
    with pytest.raises(RuntimeError):
        dp.write_steam_aliases(store, {"76561199000000001": "p1", "76561199000000002": "p2"})
    assert ("DELETE", "player_aliases", {"alias": "eq.76561199000000001"}, None) in store.calls


def test_detecta_duas_contas_do_mesmo_jogador_no_mesmo_mapa():
    s = dp.group_series(bo3_runs())[0]
    ids = {str(i): f"p{i}" for i in range(1, 11)}
    assert dp.duplicate_players(s, ids) == []
    ids["10"] = "p1"   # a segunda conta (SteamID 10) foi ligada ao jogador p1, que também joga com a conta 1
    problems = dp.duplicate_players(s, ids)
    assert len(problems) == 3 and all("duas contas" in x and "SteamID 10" in x for x in problems)


def test_temporada():
    seasons = [{"number": 1, "starts_on": "2026-10-19", "ends_on": "2026-11-18", "homologated_at": None},
               {"number": 2, "starts_on": "2026-11-19", "ends_on": "2026-12-18", "homologated_at": None},
               {"number": 0, "starts_on": "2026-01-01", "ends_on": "2026-10-18", "homologated_at": "x"}]
    assert dp.season_for(seasons, date(2026, 10, 20))["number"] == 1
    with pytest.raises(ValueError):
        dp.season_for(seasons, date(2026, 10, 10))  # temporada 0 não recebe partidas novas
    seasons[0]["homologated_at"] = "2026-11-19"
    with pytest.raises(ValueError):
        dp.season_for(seasons, date(2026, 10, 20))


def test_ids_de_partida_seguem_o_padrao_e_nao_colidem():
    s = dp.group_series(bo3_runs())[0]
    season = {"number": 1}
    existing = [{"season_number": 1, "match_format": "bo3"}, {"season_number": 1, "match_format": "bo1"},
                {"season_number": 2, "match_format": "bo3"}]
    assert dp.next_match_ids(s, season, existing, set()) == [
        "edb-t1-bo3-02-anubis", "edb-t1-bo3-02-mirage", "edb-t1-bo3-02-inferno"]
    taken = {"edb-t1-bo3-02-mirage"}
    assert dp.next_match_ids(s, season, existing, taken)[0] == "edb-t1-bo3-03-anubis"
    assert dp.next_match_ids(s, season, existing, set(), reserved=1)[0] == "edb-t1-bo3-03-anubis"


def make_plan():
    s = dp.group_series(bo3_runs())[0]
    ids = {str(i): f"p{i}" for i in range(1, 11)}
    mids = dp.next_match_ids(s, {"number": 1}, [], set())
    return dp.build_plan(s, {"number": 1}, mids, ids, "PT", "PL")


def test_plano_tem_as_linhas_certas():
    plan = make_plan()
    assert len(plan["matches"]) == 3 and len(plan["player_stats"]) == 30
    assert len(plan["details"]) == 30 and len(plan["scope"]) == 30
    m = plan["matches"][0]
    assert m["id"] == "edb-t1-bo3-01-anubis" and m["map_name"] == "Anubis" and m["rounds_total"] == 20
    assert "sha256:sha-md3_anubis_20_10_1.dem" in m["notes"]
    stat = plan["player_stats"][0]
    assert stat["won"] is None and stat["rating"] is not None and stat["kast"] == 70
    assert plan["scope"][0]["grenade_damage"] == 15 and "adr_reported" not in plan["scope"][0]
    detail = plan["details"][0]
    assert detail["weapon_kills"] == {"ak47": 10} and detail["parser_version"] == PARSER_VERSION
    bundle = plan["bundle"]
    assert bundle["format"] == "bo3" and bundle["team_a_player_ids"] == sorted(f"p{i}" for i in range(6, 11))
    assert [(x["team_a_score"], x["team_b_score"]) for x in bundle["matches"]] == [(7, 13), (13, 7), (8, 13)]
    assert all(a != b and a + b in (20, 21) for a, b in
               ((x["team_a_score"], x["team_b_score"]) for x in bundle["matches"]))


def test_plano_leva_a_linha_do_tempo_no_formato_time_a_e_b():
    plan = make_plan()
    assert [r["match_id"] for r in plan["rounds"]] == [m["id"] for m in plan["matches"]]
    # O time A é quem começou de T no mapa 1 (ids 6-10): perde 7x13 ali e vence 13x7 no mapa 2 (começa de CT).
    # A pontuação acumulada é sempre [A, B], não [T, CT].
    first = [r["winner"] for r in plan["rounds"][0]["rounds"]]
    assert len(first) == 20 and first.count("a") == 7 and first.count("b") == 13
    assert plan["rounds"][0]["rounds"][-1]["score"] == [7, 13]
    second = plan["rounds"][1]["rounds"]
    assert [r["winner"] for r in second].count("a") == 13 and second[-1]["score"] == [13, 7]
    assert all(set(r) == {"round", "winner", "side", "reason", "planted", "score"} for r in plan["rounds"][0]["rounds"])


def test_sem_linha_do_tempo_na_analise_o_plano_segue_sem_rounds():
    s = dp.group_series(bo3_runs())[0]
    for r in s.demos:
        r.analysis.pop("timeline")
    ids = {str(i): f"p{i}" for i in range(1, 11)}
    plan = dp.build_plan(s, {"number": 1}, dp.next_match_ids(s, {"number": 1}, [], set()), ids, "PT", "PL")
    assert plan["rounds"] == []


class FakeStore:
    def __init__(self, fail_on=None):
        self.calls, self.fail_on = [], fail_on

    def _api(self, method, table, params=None, payload=None):
        self.calls.append((method, table, params))
        if self.fail_on == table and method == "POST":
            raise RuntimeError("falha simulada")
        return []


def test_gravacao_na_ordem_certa():
    store = FakeStore()
    dp.write_plan(store, make_plan(), {"p10": "123"})
    assert [(m, t) for m, t, _ in store.calls] == [
        ("PATCH", "players"), ("POST", "matches"), ("POST", "player_stats"),
        ("POST", "player_match_detail"), ("POST", "player_scope_stats"), ("POST", "rpc/register_edb_confronto"),
        ("POST", "match_rounds")]


def test_linha_do_tempo_e_gravada_depois_do_confronto_e_nao_derruba_a_serie():
    store = FakeStore()
    dp.write_plan(store, make_plan())
    assert store.calls[-1][:2] == ("POST", "match_rounds")
    broken = FakeStore(fail_on="match_rounds")      # tabela ainda não criada no banco
    assert dp.write_plan(broken, make_plan()) == []
    assert not [c for c in broken.calls if c[0] == "DELETE"]


def test_falha_desfaz_tudo_em_ordem_inversa():
    store = FakeStore(fail_on="rpc/register_edb_confronto")
    with pytest.raises(RuntimeError):
        dp.write_plan(store, make_plan())
    deletes = [t for m, t, _ in store.calls if m == "DELETE"]
    assert deletes == ["player_scope_stats", "player_match_detail", "player_stats", "matches"]
    first = next(p for m, t, p in store.calls if m == "DELETE")
    assert first["match_id"].startswith("in.(edb-t1-bo3-01-anubis,")


def test_falha_logo_no_inicio_nao_apaga_nada():
    store = FakeStore(fail_on="matches")
    with pytest.raises(RuntimeError):
        dp.write_plan(store, make_plan())
    assert not [c for c in store.calls if c[0] == "DELETE"]


# --------------------------------------------------------------------------- fluxo completo do script
import importlib.util
from argparse import Namespace

_SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "edb_import.py"


def load_script():
    spec = importlib.util.spec_from_file_location("edb_import_script", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class FlowStore(FakeStore):
    def __init__(self, players):
        super().__init__()
        self._players = players

    def players(self):
        return self._players

    def matches(self):
        return []

    def stats(self):
        return []

    def _list(self, table):
        return {
            "player_aliases": [],
            "league_seasons": [{"number": 1, "starts_on": "2026-10-19", "ends_on": "2026-11-18",
                                "homologated_at": None}],
            "bo3_series": [],
        }[table]

    def save_player(self, nickname, stars=3, steamid=None, player_id=None, skill_level=None):
        self.calls.append(("SAVE_PLAYER", nickname, steamid))
        return player_id


def flow(monkeypatch, players, gravar=True, sim=True):
    script = load_script()
    monkeypatch.setattr(script, "collect", lambda folder, store, only: (bo3_runs(), []))
    store = FlowStore(players)
    args = Namespace(pasta=str(Path(__file__).parent), gravar=gravar, sim=sim, trocar_times=False,
                     time_a="PT", time_b="PL", so=None, painel=False,
                     ancora_pt=dp.DEFAULT_ANCHORS["PT"], ancora_pl=dp.DEFAULT_ANCHORS["PL"])
    script.run_once(args, store)
    return store


def writes(store):
    return [c for c in store.calls if c[0] in ("POST", "PATCH", "SAVE_PLAYER")]


def test_fluxo_previa_nao_grava(monkeypatch, capsys):
    store = flow(monkeypatch, players_db(), gravar=False)
    assert writes(store) == []
    out = capsys.readouterr().out
    assert "BO3 20/10/2026" in out and "Prévia apenas" in out


def test_fluxo_grava_serie_completa_e_vincula_nick_igual(monkeypatch, capsys):
    players = players_db()
    players[9]["nickname"] = "n10"        # mesmo nick da demo, sem SteamID: vínculo automático com --sim
    store = flow(monkeypatch, players)
    tables = [t for m, t, _ in store.calls if m in ("POST", "PATCH")]
    assert tables[0] == "players" and tables[-2:] == ["rpc/register_edb_confronto", "match_rounds"]
    assert "Vinculado automaticamente" in capsys.readouterr().out


def test_fluxo_identidade_desconhecida_nao_grava(monkeypatch, capsys):
    store = flow(monkeypatch, players_db())     # VnD não bate com o nick da demo
    assert writes(store) == []
    assert "PENDENTE" in capsys.readouterr().out


def test_fluxo_nao_grava_partida_que_ja_existe(monkeypatch, capsys):
    players = [{"id": f"p{i}", "nickname": f"Nick{i}", "steamid": str(i)} for i in range(1, 11)]
    script = load_script()
    monkeypatch.setattr(script, "collect", lambda folder, store, only: (bo3_runs(), []))
    store = FlowStore(players)
    store.matches = lambda: [{"id": "edb-t1-bo3-01-anubis", "played_at": "2026-10-20", "map_name": "Anubis"}]
    store.stats = lambda: [{"match_id": "edb-t1-bo3-01-anubis", "player_id": f"p{i}"} for i in range(1, 11)]
    args = Namespace(pasta=".", gravar=True, sim=True, trocar_times=False, time_a="PT", time_b="PL", so=None, painel=False,
                     ancora_pt=["n1"], ancora_pl=["n6"])
    script.run_once(args, store)
    assert writes(store) == []
    assert "JÁ EXISTE" in capsys.readouterr().out


# --------------------------------------------------------------------------- .gz puro e partidas já cadastradas
def test_extensao_gz_puro_e_aceita():
    f = name("md1_inferno_15_10.gz")
    assert (f.fmt, f.map, f.played_on) == ("bo1", "inferno", date(2026, 10, 15))
    assert name("md3_anubis_15_10_1.GZ").order == 1


def md1_existing(with_details=False):
    """Uma md1 de 19/10 já cadastrada (como as vindas do SCOPE), com os mesmos 10 jogadores."""
    runs = [run("md1_mirage_19_10.gz", "mirage", A, B, 13, 6)]
    series = dp.group_series(runs)[0]
    ids = {str(i): f"p{i}" for i in range(1, 11)}
    matches = [{"id": "edb-t1-bo1-01-mirage", "played_at": "2026-10-19", "map_name": "Mirage", "notes": "SCOPE"}]
    stats = [{"match_id": "edb-t1-bo1-01-mirage", "player_id": f"p{i}"} for i in range(1, 11)]
    return series, ids, matches, stats


def test_plano_de_complemento_so_tem_detalhes_e_notas():
    series, ids, matches, stats = md1_existing()
    existing = dp.existing_by_demo(series, ids, matches, stats)
    assert existing == {0: "edb-t1-bo1-01-mirage"}
    plan = dp.completion_plan(series, ids, existing, matches, set())
    assert len(plan["details"]) == 10 and plan["match_ids"] == ["edb-t1-bo1-01-mirage"]
    assert plan["details"][0]["match_id"] == "edb-t1-bo1-01-mirage"
    notes = plan["notes"]["edb-t1-bo1-01-mirage"]
    assert notes.startswith("SCOPE; demo sha256:sha-md1_mirage_19_10.gz")


def test_complemento_ignora_partida_que_ja_tem_detalhes():
    series, ids, matches, stats = md1_existing()
    existing = dp.existing_by_demo(series, ids, matches, stats)
    plan = dp.completion_plan(series, ids, existing, matches, {"edb-t1-bo1-01-mirage"})
    assert plan["match_ids"] == [] and plan["details"] == []


def test_complemento_grava_na_ordem_e_desfaz_se_falhar():
    series, ids, matches, stats = md1_existing()
    plan = dp.completion_plan(series, ids, dp.existing_by_demo(series, ids, matches, stats), matches, set())
    ok = FakeStore()
    dp.write_completion(ok, plan, {"edb-t1-bo1-01-mirage": "SCOPE"})
    assert [(m, t) for m, t, _ in ok.calls] == [("POST", "player_match_detail"), ("PATCH", "matches")]

    class FailOnPatch(FakeStore):
        def _api(self, method, table, params=None, payload=None):
            self.calls.append((method, table, params))
            if method == "PATCH" and payload and "sha256" in str(payload.get("notes")):
                raise RuntimeError("falha simulada")
            return []

    bad = FailOnPatch()
    with pytest.raises(RuntimeError):
        dp.write_completion(bad, plan, {"edb-t1-bo1-01-mirage": "SCOPE"})
    assert ("DELETE", "player_match_detail", {"match_id": "in.(edb-t1-bo1-01-mirage)"}) in bad.calls


def test_fluxo_completa_detalhes_de_partida_ja_cadastrada(monkeypatch, capsys):
    series, ids, matches, stats = md1_existing()
    players = [{"id": f"p{i}", "nickname": f"Nick{i}", "steamid": str(i)} for i in range(1, 11)]
    script = load_script()
    monkeypatch.setattr(script, "collect", lambda folder, store, only: (
        [run("md1_mirage_19_10.gz", "mirage", A, B, 13, 6)], []))
    store = FlowStore(players)
    store.matches = lambda: matches
    store.stats = lambda: stats
    store.match_details = lambda: []
    args = Namespace(pasta=".", gravar=True, sim=True, trocar_times=False, time_a="PT", time_b="PL", so=None, painel=False,
                     ancora_pt=["n1"], ancora_pl=["n6"])
    script.run_once(args, store)
    tables = [(m, t) for m, t, _ in writes(store)]
    assert tables == [("POST", "player_match_detail"), ("PATCH", "matches")]   # sem matches/player_stats/rpc
    assert "sem os dados da demo" in capsys.readouterr().out

    store2 = FlowStore(players)
    store2.matches, store2.stats = (lambda: matches), (lambda: stats)
    store2.match_details = lambda: [{"match_id": "edb-t1-bo1-01-mirage"}]
    script.run_once(args, store2)
    assert writes(store2) == []


def test_plano_com_substituicao_envia_a_lista_de_cada_mapa():
    runs = bo3_runs()
    runs[1] = run("md3_mirage_20_10_2.dem", "mirage", A[:4] + ["99"], B, 7, 13)
    s = dp.group_series(runs)[0]
    ids = {str(i): f"p{i}" for i in list(range(1, 11)) + [99]}
    anchors = {"PT": {"1"}, "PL": {"6"}}
    mids = dp.next_match_ids(s, {"number": 1}, [], set())
    plan = dp.build_plan(s, {"number": 1}, mids, ids, "PT", "PL", anchors=anchors)
    lists = [m["team_a_player_ids"] for m in plan["bundle"]["matches"]]
    assert lists[0] == sorted(f"p{i}" for i in A)
    assert lists[1] == sorted(["p1", "p2", "p3", "p4", "p99"])
    assert plan["bundle"]["team_a_player_ids"] == lists[0] and len(plan["bundle"]["team_a_player_ids"]) == 5
    assert len(plan["player_stats"]) == 30 and any(r["player_id"] == "p99" for r in plan["player_stats"])


def test_painel_gera_um_json_por_demo_sem_gravar_nada(tmp_path, capsys):
    import json
    script = load_script()
    runs = bo3_runs()
    script.export_for_panel(runs, tmp_path)
    files = sorted((tmp_path / "para_o_painel").glob("*.edb.json"))
    assert len(files) == len(runs)
    data = json.loads(files[0].read_text(encoding="utf-8"))
    assert data["kind"] == "edb-analise" and data["sha"] == runs[0].sha and data["file"] == runs[0].file.path.name
    assert data["analysis"]["players"] and "para_o_painel" in capsys.readouterr().out
