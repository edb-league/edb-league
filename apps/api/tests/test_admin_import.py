from __future__ import annotations

import io

from .conftest import ORIGIN
from .ts_contract import check

CSV = (
    "nickname,steamid,kills,deaths,assists,damage,rounds,headshots,rating,kast\n"
    "Alfa,76561198000001001,22,15,4,2100,24,10,1.25,72.5\n"
    "Bravo,,14,19,6,1500,24,5,0.92,64\n"
    "Charlie,,9,20,2,,24,3,,\n"
)


def preview_csv(client, text=CSV, name="placar.csv"):
    return client.post("/api/admin/import/preview", data={"method": "csv"},
                       files={"file": (name, io.BytesIO(text.encode("utf-8")), "text/csv")}, headers=ORIGIN)


def commit_body(preview, **overrides):
    body = {"fingerprint": preview["fingerprint"], "source": preview["source"], "played_at": "2026-11-05",
            "map_name": "Ancient", "rounds_total": preview["rounds_total"], "note": "teste",
            "players": preview["players"], "winners": ["Alfa"]}
    body.update(overrides)
    return body


def test_sample_preview_matches_contract(admin):
    response = admin.post("/api/admin/import/preview", data={"method": "sample"}, headers=ORIGIN)
    assert response.status_code == 200, response.text
    data = response.json()
    check(data, "ImportPreview")
    assert data["map"] == "Inferno" and len(data["players"]) == 10
    assert data["duplicate"] is False and data["invalid_stats"] is False and data["warnings"]
    assert all(p["nickname"] for p in data["players"])


def test_csv_preview_normalizes_rows(admin):
    response = preview_csv(admin)
    assert response.status_code == 200, response.text
    data = response.json()
    check(data, "ImportPreview")
    assert data["fingerprint"].startswith("csv_") and data["rounds_total"] == 24
    alfa, bravo, charlie = data["players"]
    assert alfa["steamid"] == "76561198000001001" and alfa["kills"] == 22 and alfa["rating"] == 1.25
    assert bravo["steamid"] == "" and charlie["damage"] is None and charlie["rating"] is None


def test_csv_preview_errors(admin):
    missing = preview_csv(admin, "nickname,kills\nA,1\n")
    assert missing.status_code == 400 and "Colunas obrigatórias" in missing.json()["detail"]
    bad_method = admin.post("/api/admin/import/preview", data={"method": "xyz"}, headers=ORIGIN)
    assert bad_method.status_code == 400
    no_file = admin.post("/api/admin/import/preview", data={"method": "csv"}, headers=ORIGIN)
    assert no_file.status_code == 400 and "CSV" in no_file.json()["detail"]
    huge = preview_csv(admin, CSV + ("X,,1,1,1,1,24,0,,\n" * 400000))
    assert huge.status_code == 400 and "5 MB" in huge.json()["detail"]


def test_preview_requires_login_and_origin(client):
    assert client.post("/api/admin/import/preview", data={"method": "sample"}, headers=ORIGIN).status_code == 401


def test_commit_saves_match_and_blocks_duplicate(admin):
    preview = preview_csv(admin).json()
    before = admin.get("/api/meta").json()["counts"]
    response = admin.post("/api/admin/import/commit", json=commit_body(preview), headers=ORIGIN)
    assert response.status_code == 200, response.text
    assert response.json() == {"ok": True, "match_id": preview["fingerprint"]}
    after = admin.get("/api/meta").json()["counts"]
    assert after["matches"] == before["matches"] + 1 and after["players"] == before["players"] + 3
    assert after["kills"] == before["kills"] + 22 + 14 + 9

    again = preview_csv(admin).json()
    assert again["duplicate"] is True
    second = admin.post("/api/admin/import/commit", json=commit_body(preview), headers=ORIGIN)
    assert second.status_code == 409 and "duplicada" in second.json()["detail"]


def test_commit_marks_winners(admin):
    preview = preview_csv(admin).json()
    admin.post("/api/admin/import/commit", json=commit_body(preview, winners=["Alfa", "Bravo"]), headers=ORIGIN)
    detail = admin.get("/api/matches/" + preview["fingerprint"]).json()
    check(detail, "MatchDetail")
    won = {row["player"]: row["won"] for row in detail["general"]}
    assert won["Alfa"] is True and won["Bravo"] is True and won["Charlie"] is False


def test_commit_validations(admin):
    preview = preview_csv(admin).json()
    players = preview["players"]
    cases = [
        ({"players": [{**players[0], "nickname": ""}, players[1]]}, "nicknames"),
        ({"players": [players[0], {**players[1], "nickname": "alfa"}]}, "duplicados"),
        ({"players": [players[0]]}, "pelo menos dois"),
        ({"played_at": "05/11/2026"}, "data real"),
        ({"rounds_total": 0}, "entre 1 e 80"),
        ({"rounds_total": 81}, "entre 1 e 80"),
        ({"fingerprint": "   "}, "Identificador"),
        ({"source": "Demo da xplay / demoparser2",
          "players": [{**p, "kills": 0, "deaths": 0} for p in players]}, "erro de leitura"),
    ]
    for override, expected in cases:
        response = admin.post("/api/admin/import/commit", json=commit_body(preview, **override), headers=ORIGIN)
        assert response.status_code == 400, (override, response.text)
        assert expected in response.json()["detail"], (override, response.json())
    assert admin.post("/api/admin/import/commit", json={"fingerprint": "x"}, headers=ORIGIN).status_code == 422


def test_commit_keeps_existing_player_stars(admin):
    players = admin.get("/api/admin/overview").json()["players"]
    veteran = next(p for p in players if p["stars"] == 5)
    preview = preview_csv(admin, CSV.replace("Alfa", veteran["nickname"])).json()
    admin.post("/api/admin/import/commit", json=commit_body(preview, winners=[]), headers=ORIGIN)
    after = admin.get("/api/admin/overview").json()["players"]
    assert next(p for p in after if p["id"] == veteran["id"])["stars"] == 5
    assert len([p for p in after if p["nickname"].casefold() == veteran["nickname"].casefold()]) == 1


def test_commit_in_local_sqlite(local_admin):
    preview = preview_csv(local_admin).json()
    response = local_admin.post("/api/admin/import/commit", json=commit_body(preview), headers=ORIGIN)
    assert response.status_code == 200, response.text
    assert len(local_admin.get("/api/players").json()) == 3
    assert local_admin.post("/api/admin/import/commit", json=commit_body(preview), headers=ORIGIN).status_code == 409


def test_exports_are_csv_with_bom(admin):
    for kind, filename in (("players", "jogadores"), ("matches", "partidas"), ("stats", "estatisticas")):
        response = admin.get(f"/api/admin/export/{kind}.csv")
        assert response.status_code == 200, kind
        assert response.headers["content-type"].startswith("text/csv")
        assert filename in response.headers["content-disposition"]
        assert response.content.startswith(b"\xef\xbb\xbf")
        assert len(response.content.splitlines()) > 1
    assert admin.get("/api/admin/export/players.csv").text.count("\n") >= 15
    assert admin.get("/api/admin/export/outro.csv").status_code == 404


def test_exports_require_login(client):
    assert client.get("/api/admin/export/players.csv").status_code == 401
