from __future__ import annotations

from .conftest import ORIGIN
from .test_admin_import import commit_body
from .ts_contract import check


def sample_preview(admin):
    return admin.post("/api/admin/import/preview", data={"method": "sample"}, headers=ORIGIN).json()


def new_candidate(admin, played_at="2026-11-05"):
    preview = sample_preview(admin)
    response = admin.post("/api/admin/import/commit", json=commit_body(preview, played_at=played_at, winners=[]),
                          headers=ORIGIN)
    assert response.status_code == 200, response.text
    return preview["fingerprint"]


def test_homologation_blocked_in_local_mode(local_admin):
    response = local_admin.post("/api/admin/seasons/1/homologate", headers=ORIGIN)
    assert response.status_code == 400 and "Supabase" in response.json()["detail"]


def test_confront_blocked_in_local_mode(local_admin):
    assert local_admin.get("/api/admin/confront/candidates?season=1").status_code == 400
    body = {"season": 1, "format": "bo1", "match_ids": ["a"], "team_a_ids": [], "scores": {"a": [13, 5]},
            "team_a_name": "PT", "team_b_name": "PL"}
    response = local_admin.post("/api/admin/confront", json=body, headers=ORIGIN)
    assert response.status_code == 400 and "Supabase" in response.json()["detail"]


def test_homologation_requires_closed_pending_season(admin):
    assert admin.post("/api/admin/seasons/1/homologate", headers=ORIGIN).status_code == 404  # ainda ativa
    assert admin.post("/api/admin/seasons/0/homologate", headers=ORIGIN).status_code == 404
    assert admin.post("/api/admin/seasons/99/homologate", headers=ORIGIN).status_code == 404
    assert admin.post("/api/admin/seasons/abc/homologate", headers=ORIGIN).status_code == 422


def test_homologation_rejects_incomplete_series(admin, monkeypatch):
    monkeypatch.setenv("EDB_TODAY", "2026-11-20")
    admin.get("/api/meta")
    from edb_api import service
    service.get_service().invalidate()
    overview = admin.get("/api/admin/overview").json()
    check(overview, "AdminOverview")
    assert [s["number"] for s in overview["pending_seasons"]] == [1]
    response = admin.post("/api/admin/seasons/1/homologate", headers=ORIGIN)
    assert response.status_code == 400
    assert response.json()["detail"].startswith("Homologação não realizada: ")
    assert "incompletos" in response.json()["detail"]
    assert admin.get("/api/meta").json()["seasons"][1]["homologated"] is False


def test_homologation_success_after_closing_pending_series(admin, monkeypatch):
    monkeypatch.setenv("EDB_TODAY", "2026-11-20")
    from edb_api import service
    svc = service.get_service()
    data = svc.store.data
    dropped = {s["id"] for s in data["bo3_series"] if s["season_number"] == 1 and s["status"] != "completed"}
    assert dropped
    data["bo3_series"] = [s for s in data["bo3_series"] if s["id"] not in dropped]
    data["bo3_maps"] = [m for m in data["bo3_maps"] if m["series_id"] not in dropped]
    svc.invalidate()
    response = admin.post("/api/admin/seasons/1/homologate", headers=ORIGIN)
    assert response.status_code == 200, response.text
    assert response.json() == {"ok": True}
    meta = admin.get("/api/meta").json()
    assert meta["seasons"][1]["homologated"] is True and meta["seasons"][1]["status"] == "homologated"
    ranking = admin.get("/api/rankings/elite?season=1").json()
    check(ranking, "Ranking")
    assert admin.get("/api/admin/overview").json()["pending_seasons"] == []
    titles = [t for t in admin.get("/api/hall-of-fame").json()["titles"] if t["season_number"] == 1]
    assert len(titles) == 3


def test_confront_candidates_and_registration(admin):
    first = new_candidate(admin)
    candidates = admin.get("/api/admin/confront/candidates?season=1").json()
    check(candidates, "ConfrontCandidates")
    assert [m["id"] for m in candidates["maps"]] == [first]
    assert len(candidates["maps"][0]["player_ids"]) == 10 and len(candidates["players"]) == 10
    ids = [p["id"] for p in candidates["players"]]
    before = admin.get("/api/matches?season=1").json()
    body = {"season": 1, "format": "bo1", "match_ids": [first], "team_a_ids": ids[:5],
            "scores": {first: [13, 4]}, "team_a_name": "PT", "team_b_name": "PL"}
    response = admin.post("/api/admin/confront", json=body, headers=ORIGIN)
    assert response.status_code == 200, response.text
    assert response.json() == {"ok": True}
    after = admin.get("/api/matches?season=1").json()
    check(after, "MatchesList")
    assert len(after["bo1"]) == len(before["bo1"]) + 1
    assert admin.get("/api/admin/confront/candidates?season=1").json()["maps"] == []


def test_confront_validations(admin):
    first = new_candidate(admin)
    ids = [p["id"] for p in admin.get("/api/admin/confront/candidates?season=1").json()["players"]]
    base = {"season": 1, "format": "bo1", "match_ids": [first], "team_a_ids": ids[:5],
            "scores": {first: [13, 4]}, "team_a_name": "PT", "team_b_name": "PL"}
    missing_score = admin.post("/api/admin/confront", json={**base, "scores": {}}, headers=ORIGIN)
    assert missing_score.status_code == 400 and "placar" in missing_score.json()["detail"]
    bad_pair = admin.post("/api/admin/confront", json={**base, "scores": {first: [13]}}, headers=ORIGIN)
    assert bad_pair.status_code == 422
    closed = admin.post("/api/admin/confront", json={**base, "season": 0}, headers=ORIGIN)
    assert closed.status_code == 404
    assert admin.get("/api/admin/confront/candidates?season=0").status_code == 404
    assert admin.get("/api/admin/confront/candidates?season=99").status_code == 404
    assert admin.get("/api/admin/confront/candidates").status_code == 422
    # BO1 com placar empatado ou time sem jogadores é recusado pelas regras de confront_registry.
    tie = admin.post("/api/admin/confront", json={**base, "scores": {first: [10, 10]}}, headers=ORIGIN)
    assert tie.status_code == 400
    empty = admin.post("/api/admin/confront", json={**base, "team_a_ids": []}, headers=ORIGIN)
    assert empty.status_code == 400


def test_steam_view_without_key_is_no_key(demo):
    from edb_api import views
    detail = views.build_player_detail(demo, demo.snap(), demo.snap().players[0]["id"])
    check(detail["steam"], "SteamView")
    assert detail["steam"]["state"] in ("no_key", "unlinked")
