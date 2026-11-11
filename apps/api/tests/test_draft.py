from __future__ import annotations

from .conftest import ORIGIN


def post(client, path, **kwargs):
    return client.post(path, headers=ORIGIN, **kwargs)


def ids(client, count):
    players = client.get("/api/players").json()
    return [p["id"] for p in players][:count]


def create(admin, teams=3, size=4):
    chosen = ids(admin, teams * size)
    body = {"name": "Copa EDB", "team_size": size,
            "teams": [{"name": f"Time {i + 1}", "captain_id": chosen[i]} for i in range(teams)],
            "pool_ids": chosen[teams:]}
    return post(admin, "/api/admin/draft", json=body), chosen


def test_draft_is_empty_then_flows_to_the_end(admin):
    assert admin.get("/api/draft").json() == {"exists": False}
    assert admin.get("/api/draft").headers["cache-control"] == "no-store"
    created, chosen = create(admin)
    assert created.status_code == 200, created.text
    view = created.json()
    assert view["exists"] and view["status"] == "drafting" and len(view["available"]) == 9
    assert view["next"] == {"number": 1, "total": 9, "team_id": 1, "team_name": "Time 1"}
    assert [t["captain"]["id"] for t in view["teams"]] == chosen[:3]

    for pid in chosen[3:]:
        view = post(admin, "/api/admin/draft/pick", json={"player_id": pid}).json()
    assert view["status"] == "done" and view["next"] is None and view["available"] == []
    # cobra: o time 3 escolhe duas vezes seguidas (picks 3 e 4)
    assert [p["number"] for p in view["teams"][2]["picks"]] == [3, 4, 9]
    assert all(len(t["picks"]) == 3 for t in view["teams"])
    assert admin.get("/api/draft").json()["status"] == "done"


def test_undo_and_reset(admin):
    _, chosen = create(admin)
    post(admin, "/api/admin/draft/pick", json={"player_id": chosen[3]})
    view = post(admin, "/api/admin/draft/undo").json()
    assert view["picks_made"] == 0 and view["next"]["number"] == 1
    assert post(admin, "/api/admin/draft/undo").status_code == 400
    assert admin.delete("/api/admin/draft", headers=ORIGIN).json() == {"exists": False}
    assert admin.get("/api/draft").json() == {"exists": False}


def test_errors(admin):
    assert post(admin, "/api/admin/draft/pick", json={"player_id": "x"}).status_code == 404
    created, chosen = create(admin)
    assert created.status_code == 200
    again = post(admin, "/api/admin/draft", json={
        "name": "Outro", "team_size": 2, "teams": [{"name": "A", "captain_id": chosen[0]}, {"name": "B", "captain_id": chosen[1]}],
        "pool_ids": chosen[2:4]})
    assert again.status_code == 400  # já existe um draft
    assert post(admin, "/api/admin/draft/pick", json={"player_id": chosen[0]}).status_code == 400  # capitão
    assert post(admin, "/api/admin/draft/pick", json={"player_id": "inexistente"}).status_code == 400


def test_draft_requires_admin_and_validates_players(client, admin):
    anonymous = type(client)(client.app)
    for method, path in (("post", "/api/admin/draft"), ("post", "/api/admin/draft/pick"),
                         ("post", "/api/admin/draft/undo"), ("delete", "/api/admin/draft")):
        assert getattr(anonymous, method)(path, headers=ORIGIN).status_code in (401, 403)
    bad = post(admin, "/api/admin/draft", json={"name": "Copa", "team_size": 2,
               "teams": [{"name": "A", "captain_id": "nao-existe"}, {"name": "B", "captain_id": "tambem-nao"}],
               "pool_ids": ["a", "b"]})
    assert bad.status_code == 400 and "ativos" in bad.json()["detail"]


def test_draft_persists_in_sqlite(local_admin, local):
    for nick in "ABCDEF":
        local.store.save_player(nick, 3, None, skill_level=5)
    local.invalidate()
    players = [p["id"] for p in local_admin.get("/api/players").json()]
    body = {"name": "Local", "team_size": 3, "teams": [{"name": "X", "captain_id": players[0]},
            {"name": "Y", "captain_id": players[1]}], "pool_ids": players[2:6]}
    assert post(local_admin, "/api/admin/draft", json=body).status_code == 200
    assert post(local_admin, "/api/admin/draft/pick", json={"player_id": players[2]}).status_code == 200
    saved = local.store.draft_get()
    assert saved["picks"][0]["player_id"] == players[2]
