"""A lista de confrontos sai da data mais recente para a mais antiga, não na ordem de cadastro."""
from __future__ import annotations

from types import SimpleNamespace

from edb_api import views


def _snap(series, bo3_maps, matches):
    return SimpleNamespace(
        resolve_season=lambda s: 1,
        season_row=lambda n: {"number": n, "label": f"Temporada {n}"},
        seasons=[{"number": 1, "label": "Temporada 1", "starts_on": "2026-10-15", "ends_on": "2026-11-18"}],
        matches=matches, bo3_maps=bo3_maps, bo3=series, stats=[], players=[], active_players=[],
    )


def _game(mid, day):
    return {"id": mid, "map_name": "Mirage", "played_at": f"2026-10-{day:02d}", "team_a_score": 13,
            "team_b_score": 5, "team_a_name": "PT", "team_b_name": "PL", "rounds_total": 18}


def _series(sid, seq, fmt="bo1"):
    return {"id": sid, "season_number": 1, "sequence_number": seq, "status": "completed",
            "winner_side": "a", "match_format": fmt, "team_a_name": "PT", "team_b_name": "PL"}


def test_confrontos_ficam_do_mais_recente_para_o_mais_antigo(monkeypatch):
    monkeypatch.setattr(views, "season_by_number", lambda snap, n: {"number": n})
    # Ordem de cadastro (sequence_number) propositalmente diferente da ordem das datas.
    days = {"a": 19, "b": 15, "c": 20, "d": 19}
    matches = [_game("m" + k, d) for k, d in days.items()]
    series = [_series(k, i + 1) for i, k in enumerate(days)]
    maps = [{"series_id": k, "match_id": "m" + k, "map_number": 1, "winner_side": "a"} for k in days]
    out = views.build_matches(_snap(series, maps, matches), 1)
    assert [c["id"] for c in out["bo1"]] == ["c", "d", "a", "b"]  # 20, 19 (cadastrado depois), 19, 15
