"""Importação de série pelo painel: prévia com análises, escolhas de identidade e gravação."""
from __future__ import annotations

import io
import json

from edb import demo_pipeline as dp
from edb.demo_stats import COUNT_FIELDS

from .conftest import ORIGIN
from .ts_contract import check

# Os dois primeiros são jogadores da base de demonstração (Falcão e Nebulosa); o resto é novo para o banco.
A_IDS = ["76561198000000101", "76561198000000104", "76561198000009003", "76561198000009004", "76561198000009005"]
B_IDS = [f"7656119800000920{i}" for i in range(5)]
SHA = {1: "a" * 64, 2: "b" * 64, 3: "c" * 64}


def player(steam, team, rounds):
    row = {f: 0 for f in COUNT_FIELDS}
    row.update(steamid=steam, nick=f"nick{steam[-4:]}", team=team, rounds=rounds, kills=15, deaths=12, assists=3,
               damage=1500, headshots=6, plants=0, defuses=0, kast=70, open_kills=2, trade_kills=1,
               rounds_t=rounds // 2, rounds_ct=rounds - rounds // 2, kills_t=7, kills_ct=8, deaths_t=6, deaths_ct=6,
               damage_t=700, damage_ct=800, kast_rounds_t=7, kast_rounds_ct=7, weapon_kills={"ak47": 10},
               clutches={"1v1": [1, 0]})
    return row


def analysis(map_name, t_ids, ct_ids, t_score, ct_score):
    rounds = t_score + ct_score
    return {"parser_version": 3, "map": map_name, "server": "XPLAY.GG", "rounds": rounds, "overtime": False,
            "warnings": [], "score": {"team_t_first": t_score, "team_ct_first": ct_score},
            "rosters": {"team_t_first": t_ids, "team_ct_first": ct_ids},
            "players": [player(s, 2, rounds) for s in t_ids] + [player(s, 3, rounds) for s in ct_ids]}


def export(file, sha, data):
    return {"kind": "edb-analise", "file": file, "sha": sha, "analysis": data}


def upload(name, content):
    return ("files", (name, io.BytesIO(json.dumps(content).encode("utf-8")), "application/json"))


def bo3_files(a_wins_second=True):
    """md3 2x0 do time A (quem começou de T no mapa 1)."""
    first = export("md3_inferno_25_10_1.dem", SHA[1], analysis("inferno", A_IDS, B_IDS, 13, 6))
    second = export("md3_mirage_25_10_2.dem", SHA[2], analysis("mirage", B_IDS, A_IDS, 8, 13))
    return [upload("md3_inferno_25_10_1.edb.json", first), upload("md3_mirage_25_10_2.edb.json", second)]


def preview(client, files, **form):
    return client.post("/api/admin/import/series/preview", data=form, files=files, headers=ORIGIN)


def choices_for(pending):
    return {item["steamid"]: {"kind": "new", "nickname": f"Novo {item['steamid'][-4:]}"} for item in pending}


def commit_body(item, **extra):
    body = {"payload": item["payload"], "team_a": "PT", "team_b": "PL", "swap": False,
            "choices": choices_for(item["unresolved"])}
    body.update(extra)
    return body


def test_preview_reads_bo3_and_asks_who_is_unknown(admin):
    response = preview(admin, bo3_files())
    assert response.status_code == 200, response.text
    data = response.json()
    check(data, "SeriesPreview")
    assert data["notes"] == [] and len(data["series"]) == 1
    item = data["series"][0]
    assert item["format"] == "bo3" and item["problems"] == [] and item["can_commit"] is True
    assert item["played_on"].endswith("-10-25") and item["season"] == 1
    assert [m["map"] for m in item["maps"]] == ["Inferno", "Mirage"]
    assert [(m["score_a"], m["score_b"]) for m in item["maps"]] == [(13, 6), (13, 8)]
    # A é o time que começou de T no mapa 1; no mapa 2 ele começou de CT.
    assert {p["steamid"] for p in item["maps"][1]["players"] if p["team"] == "A"} == set(A_IDS)
    known = {p["steamid"]: p["player"] for m in item["maps"] for p in m["players"] if p["player"]}
    assert set(known) == {A_IDS[0], A_IDS[1]}
    assert {u["steamid"] for u in item["unresolved"]} == set(A_IDS[2:]) | set(B_IDS)


def test_preview_reports_bad_files_without_losing_the_good_ones(admin):
    files = bo3_files() + [
        upload("md3_nuke_25_10_3.edb.json", {"kind": "outro"}),
        ("files", ("partida.txt", io.BytesIO(b"x"), "text/plain")),
    ]
    data = preview(admin, files).json()
    assert len(data["series"]) == 1
    assert any("importador da liga" in n for n in data["notes"]) and any("partida.txt" in n for n in data["notes"])


def test_preview_flags_incomplete_series_and_missing_files(admin):
    one = preview(admin, bo3_files()[:1]).json()
    assert any("incompleta" in p for p in one["series"][0]["problems"]) and one["series"][0]["can_commit"] is False
    empty = admin.post("/api/admin/import/series/preview", data={}, headers=ORIGIN)
    assert empty.status_code == 400 and "Envie" in empty.json()["detail"]


def test_preview_requires_login(client):
    assert preview(client, bo3_files()).status_code == 401


def test_commit_saves_series_with_details_and_blocks_a_second_time(admin):
    item = preview(admin, bo3_files()).json()["series"][0]
    before = admin.get("/api/meta").json()["counts"]
    response = admin.post("/api/admin/import/series/commit", json=commit_body(item), headers=ORIGIN)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["ok"] and len(data["match_ids"]) == 2 and data["match_ids"][0].startswith("edb-t1-bo3-")
    after = admin.get("/api/meta").json()["counts"]
    assert after["matches"] == before["matches"] + 2 and after["players"] == before["players"] + 8

    from edb_api.service import get_service
    store = get_service().store
    saved = {m["id"]: m for m in store.matches()}
    assert f"sha256:{SHA[1]}" in saved[data["match_ids"][0]]["notes"]
    assert {d["match_id"] for d in store.match_details()} >= set(data["match_ids"])
    series = [s for s in store._list("bo3_series") if s["match_format"] == "bo3" and s["season_number"] == 1][-1]
    assert series["winner_side"] == "a" and series["team_a_name"] == "PT"

    again = preview(admin, bo3_files()).json()
    assert again["series"] == [] and sum("já importada" in n for n in again["notes"]) == 2
    repeated = admin.post("/api/admin/import/series/commit", json=commit_body(item), headers=ORIGIN)
    assert repeated.status_code == 409 and "já foi importada" in repeated.json()["detail"]


def test_commit_needs_an_answer_for_every_unknown_account(admin):
    item = preview(admin, bo3_files()).json()["series"][0]
    partial = commit_body(item)
    partial["choices"].pop(B_IDS[0])
    response = admin.post("/api/admin/import/series/commit", json=partial, headers=ORIGIN)
    assert response.status_code == 400 and "Diga quem é" in response.json()["detail"]
    clash = commit_body(item)
    clash["choices"][B_IDS[0]] = {"kind": "new", "nickname": "falcão"}
    response = admin.post("/api/admin/import/series/commit", json=clash, headers=ORIGIN)
    assert response.status_code == 400 and "Já existe um jogador" in response.json()["detail"]


def test_commit_links_to_free_player_and_registers_second_account(admin):
    data = preview(admin, bo3_files()).json()
    item, directory = data["series"][0], {p["nickname"]: p for p in data["players"]}
    free = directory["Tubarão"]            # sem SteamID na base de demonstração
    registered = directory["Cobra"]
    assert not free["has_steamid"]
    body = commit_body(item)
    body["choices"][B_IDS[0]] = {"kind": "link", "player_id": free["id"]}
    wrong = {**body, "choices": {**body["choices"], B_IDS[1]: {"kind": "alias", "player_id": registered["id"]}}}
    # Cobra não tem SteamID: não dá para ser "outra conta" dele.
    bad = admin.post("/api/admin/import/series/commit", json=wrong, headers=ORIGIN)
    assert bad.status_code == 400 and "ainda não tem SteamID" in bad.json()["detail"]
    ok = admin.post("/api/admin/import/series/commit", json=body, headers=ORIGIN)
    assert ok.status_code == 200, ok.text
    from edb_api.service import get_service
    players = {p["nickname"]: p for p in get_service().store.players()}
    assert players["Tubarão"]["steamid"] == B_IDS[0]


def test_failed_write_leaves_no_new_players_or_aliases(admin, monkeypatch):
    item = preview(admin, bo3_files()).json()["series"][0]
    from edb_api.service import get_service
    store = get_service().store
    players_before = len(store.players())

    def boom(*_args, **_kwargs):
        raise RuntimeError("banco indisponível")

    monkeypatch.setattr(dp, "write_plan", boom)
    response = admin.post("/api/admin/import/series/commit", json=commit_body(item), headers=ORIGIN)
    assert response.status_code == 502 and "nada ficou salvo" in response.json()["detail"]
    assert len(store.players()) == players_before and store._list("player_aliases") == []


def test_commit_rejects_tampered_payload(admin):
    for payload in ("", "nao-e-base64!", "eJw="):
        response = admin.post("/api/admin/import/series/commit",
                              json={"payload": payload, "choices": {}}, headers=ORIGIN)
        assert response.status_code == 400, payload


def test_commit_needs_online_database(local_admin):
    response = local_admin.post("/api/admin/import/series/preview", files=bo3_files(), headers=ORIGIN)
    assert response.status_code == 400 and "online" in response.json()["detail"]


def test_single_demo_preview_suggests_date_from_file_name_and_detects_known_sha(admin, monkeypatch):
    from edb.demo_importer import DemoOutput
    from edb_api import admin_ops

    players = [{"nickname": f"P{i}", "steamid": str(76561198000009500 + i), "kills": 10 + i, "deaths": 12,
                "assists": 2, "damage": 1500, "rounds": 22, "headshots": 4, "plants": 0, "defuses": 0,
                "rating": 1.1, "kast": 70, "open_kills": 1, "trade_kills": 1, "won": i < 5} for i in range(10)]
    monkeypatch.setattr(admin_ops, "parse_demo_stats",
                        lambda path, fingerprint: DemoOutput(fingerprint, "Inferno", 22, players, []))
    content = b"PBDEMS2" + b"1" * 3000

    def send(name):
        return admin.post("/api/admin/import/preview", data={"method": "demo"},
                          files={"file": (name, io.BytesIO(content), "application/octet-stream")}, headers=ORIGIN)

    data = send("md1_inferno_25_10.dem").json()
    check(data, "ImportPreview")
    assert data["played_at"].endswith("-10-25") and data["duplicate"] is False and data["warnings"] == []
    odd = send("minha_partida.dem").json()
    assert odd["played_at"] is None and any("padrão" in w for w in odd["warnings"])
    wrong_map = send("md1_mirage_25_10.dem").json()
    assert any("diz mirage" in w for w in wrong_map["warnings"])

    body = {"fingerprint": data["fingerprint"], "source": data["source"], "played_at": data["played_at"],
            "map_name": "Inferno", "rounds_total": 22, "note": "", "players": data["players"], "winners": []}
    assert admin.post("/api/admin/import/commit", json=body, headers=ORIGIN).status_code == 200
    from edb_api.service import get_service
    saved = next(m for m in get_service().store.matches() if m["id"] == data["fingerprint"])
    assert saved["notes"] == f"sha256:{data['fingerprint']}"
    assert send("md1_inferno_25_10.dem").json()["duplicate"] is True
