"""Perfil estilo HLTV: fórmulas públicas, divisões por zero e notas relativas."""
import os

import pytest

from edb.hltv_stats import aggregate, build_league, build_profile, percentile_scores, rating1, rating2


def row(**over):
    base = {"rounds_t": 10, "rounds_ct": 10, "kills_t": 8, "kills_ct": 9, "deaths_t": 6, "deaths_ct": 7,
            "assists_t": 1, "assists_ct": 2, "damage_t": 700, "damage_ct": 800, "kast_rounds_t": 7, "kast_rounds_ct": 7,
            "rk1_t": 4, "rk2_t": 2, "rk1_ct": 5, "rk2_ct": 2, "rk3_ct": 0, "rounds_won": 11, "kills_in_won_rounds": 10,
            "weapon_kills": {"ak47": 12, "awp": 5}, "clutches": {"1v1": [2, 1]}}
    base.update(over)
    return base


def test_rating1_reproduz_o_valor_publicado_da_hltv():
    # Totais da página de estatísticas do FalleN na HLTV: Rating 1.0 = 1.03.
    rows = [{"rounds_t": 58564, "kills_t": 39182, "deaths_t": 35836,
             "rk1_t": 17455, "rk2_t": 7035, "rk3_t": 1999, "rk4_t": 364, "rk5_t": 40}]
    assert rating1(aggregate(rows)) == pytest.approx(1.03, abs=0.01)


def test_rating2_usa_a_formula_publica():
    t = aggregate([row()])
    # Cálculo manual: KAST 70, KPR 0,85, DPR 0,65, APR 0,15, ADR 75.
    impact = 2.13 * 0.85 + 0.42 * 0.15 - 0.41
    esperado = 0.0073 * 70 + 0.3591 * 0.85 - 0.5329 * 0.65 + 0.2372 * impact + 0.0032 * 75 + 0.1587
    assert rating2(t) == pytest.approx(esperado)


def test_perfil_vazio_e_sem_rounds_viram_none():
    assert build_profile([]) is None
    assert build_profile([row(rounds_t=0, rounds_ct=0)]) is None


def test_divisoes_por_zero_nao_quebram():
    profile = build_profile([{"rounds_t": 5, "rounds_ct": 5}])
    assert profile is not None
    metrics = {m["key"]: m for ms in profile["sections"].values() for m in ms}
    assert metrics["kpr"]["value"] == 0
    assert metrics["deaths_traded"]["value"] is None
    assert metrics["opening_ratio"]["value"] is None
    assert profile["clutches"][0] == {"label": "1v1", "tries": 0, "won": 0}


def test_lados_somam_o_total():
    profile = build_profile([row()])
    kpr = next(m for m in profile["sections"]["firepower"] if m["key"] == "kpr")
    assert kpr["value"] == pytest.approx(0.85)
    assert kpr["t"] == pytest.approx(0.8) and kpr["ct"] == pytest.approx(0.9)
    assert profile["totals"]["kills"] == profile["totals"]["kills_t"] + profile["totals"]["kills_ct"] == 17


def test_notas_relativas_exigem_pelo_menos_tres_jogadores():
    duo = build_league({"a": [row()], "b": [row(kills_t=1, kills_ct=1)]})
    assert all(s["value"] is None for s in duo["a"]["scores"])
    quarteto = build_league({k: [row(kills_t=n, kills_ct=n, rounds_t=50, rounds_ct=50)]
                             for k, n in zip("abcd", (2, 4, 8, 12))})
    firepower = {pid: next(s["value"] for s in p["scores"] if s["key"] == "firepower") for pid, p in quarteto.items()}
    assert firepower["d"] > firepower["c"] > firepower["b"] > firepower["a"]
    assert all(len(p["similar"]) == 3 for p in quarteto.values())


def test_notas_exigem_100_rounds_e_amostra_pequena_nao_distorce_os_outros():
    cheios = {k: [row(kills_t=n, kills_ct=n, rounds_t=50, rounds_ct=50)] for k, n in zip("abc", (20, 40, 60))}
    sem_novato = build_league(cheios)
    # Um jogador com 1 mapa (20 rounds) e números absurdos: não recebe nota e não muda a dos outros.
    novato = {"n": [row(kills_t=19, kills_ct=19)]}
    com_novato = build_league({**cheios, **novato})
    assert all(s["value"] is None for s in com_novato["n"]["scores"])
    assert [s["value"] for s in com_novato["b"]["scores"]] == [s["value"] for s in sem_novato["b"]["scores"]]
    assert all(s["player_id"] != "n" for p in com_novato.values() for s in p["similar"])
    # Perfil por lado conta metade do mínimo (50 rounds do lado).
    por_lado = build_league({k: [row(kills_t=n, kills_ct=n, rounds_t=50, rounds_ct=50)]
                             for k, n in zip("abc", (20, 40, 60))}, side="t")
    assert por_lado["a"]["scores"][0]["value"] is not None


def test_percentil_com_empate():
    assert percentile_scores({"a": {"sections": {}}}) == {"a": {s: None for s in
            ("firepower", "entrying", "trading", "opening", "closing", "sniping", "utility")}}


@pytest.mark.skipif(not os.environ.get("EDB_TEST_DEMO"), reason="defina EDB_TEST_DEMO com o caminho de uma .dem")
def test_demo_real_fecha_as_contas_internas():
    from edb.demo_stats import analyze
    result = analyze(os.environ["EDB_TEST_DEMO"])
    players, rounds = result["players"], result["rounds"]
    assert sum(p["open_kills"] for p in players) == rounds
    assert all(p["rounds_t"] + p["rounds_ct"] == rounds for p in players)
    assert all(sum(p["weapon_kills"].values()) == p["kills"] for p in players)
    assert sum(p["damage"] for p in players) == sum(p["damage_taken"] for p in players)


def test_nomes_em_ingles_com_significado_em_portugues():
    profile = build_profile([row()])
    kpr = next(m for m in profile["sections"]["firepower"] if m["key"] == "kpr")
    assert kpr["label"] == "Kills per round" and kpr["meaning"] == "kills por round"
    for metrics in profile["sections"].values():
        assert all(m["label"] and m["meaning"] and m["label"] != m["meaning"] for m in metrics)
    assert all(c["meaning"] for c in profile["cards"])
    league = build_league({k: [row()] for k in "abc"})
    assert league["a"]["scores"][0]["label"] == "Firepower" and league["a"]["scores"][0]["meaning"] == "poder de fogo"


def test_lado_usa_so_os_rounds_do_lado():
    t_side = build_profile([row()], "t")
    assert t_side["side"] == "t" and t_side["rounds"] == 10
    kpr = next(m for m in t_side["sections"]["firepower"] if m["key"] == "kpr")
    assert kpr["value"] == pytest.approx(0.8)
    assert t_side["totals"]["kills"] == 8
    # métrica que a demo não separa por lado fica sem valor em vez de repetir o total
    kprw = next(m for m in t_side["sections"]["firepower"] if m["key"] == "kprw")
    assert kprw["value"] is None
    assert t_side["rating"]["rating1"] == pytest.approx(rating1(aggregate([row()]), "t"), abs=0.01)


def test_perfil_vazio_tem_a_mesma_forma_do_real():
    from edb.hltv_stats import empty_profile
    empty, real = empty_profile("ct"), build_profile([row()])
    assert set(empty) <= set(real) | {"scores", "similar"}
    assert empty["rounds"] == 0 and empty["side"] == "ct"
    assert set(empty["sections"]) == set(real["sections"])
