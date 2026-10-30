"""Tabela de mapas do jogador: ADR ponderado por rounds, vitória desconhecida fora da taxa."""
from edb_api.views import _per_map


def record(rounds, damage, won=True, kills=10, adr=None):
    return {"map": "Inferno", "rounds": rounds, "damage": damage, "won": won, "kills": kills,
            "adr": adr if adr is not None else (damage / rounds if damage is not None else None), "rating": 1.0}


def test_adr_is_total_damage_over_total_rounds():
    # 2000 de dano em 20 rounds (100) e 3000 em 30 rounds (100) não depende do peso; aqui o peso muda tudo:
    # média simples dos ADRs = (100 + 50) / 2 = 75; ponderado = (2000 + 1500) / (20 + 30) = 70.
    (row,) = _per_map([record(20, 2000), record(30, 1500)])
    assert row["adr"] == 70.0 and row["kpr"] == 0.4


def test_adr_ignores_matches_without_damage_and_falls_back_to_reported_adr():
    (row,) = _per_map([record(20, 2000), record(30, None, adr=None)])
    assert row["adr"] == 100.0
    (only_adr,) = _per_map([record(20, None, adr=80.0), record(30, None, adr=60.0)])
    assert only_adr["adr"] == 70.0


def test_unknown_winner_is_left_out_of_win_rate():
    (row,) = _per_map([record(20, 2000, won=True), record(20, 2000, won=False), record(20, 2000, won=None)])
    assert row["games"] == 3 and row["wins"] == 1 and row["win_rate"] == 50.0
