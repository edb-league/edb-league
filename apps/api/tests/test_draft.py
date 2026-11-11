from __future__ import annotations

from .conftest import ORIGIN


def post(client, path, **kwargs):
    return client.post(path, headers=ORIGIN, **kwargs)


def ids(client, count):
    players = client.get("/api/players").json()
    return [p["id"] for p in players][:count]


def create(client, teams=3, size=4):
    chosen = ids(client, teams * size)
    body = {"name": "Copa EDB", "team_size": size,
            "teams": [{"name": f"Time {i + 1}", "captain_id": chosen[i]} for i in range(teams)],
            "pool_ids": chosen[teams:]}
    return post(client, "/api/draft", json=body), chosen


def test_draft_is_empty_then_flows_to_the_end(client):
    assert client.get("/api/draft").json() == {"exists": False}
    assert client.get("/api/draft").headers["cache-control"] == "no-store"
    created, chosen = create(client)
    assert created.status_code == 200, created.text
    view = created.json()
    assert view["exists"] and view["status"] == "drafting" and len(view["available"]) == 9
    assert view["next"] == {"number": 1, "total": 9, "team_id": 1, "team_name": "Time 1"}
    assert [t["captain"]["id"] for t in view["teams"]] == chosen[:3]

    for pid in chosen[3:]:
        view = post(client, "/api/draft/pick", json={"player_id": pid}).json()
    assert view["status"] == "done" and view["next"] is None and view["available"] == []
    # cobra: o time 3 escolhe duas vezes seguidas (picks 3 e 4)
    assert [p["number"] for p in view["teams"][2]["picks"]] == [3, 4, 9]
    assert all(len(t["picks"]) == 3 for t in view["teams"])
    assert client.get("/api/draft").json()["status"] == "done"


def test_undo_and_reset(client):
    _, chosen = create(client)
    post(client, "/api/draft/pick", json={"player_id": chosen[3]})
    view = post(client, "/api/draft/undo").json()
    assert view["picks_made"] == 0 and view["next"]["number"] == 1
    assert post(client, "/api/draft/undo").status_code == 400
    assert client.delete("/api/draft", headers=ORIGIN).json() == {"exists": False}
    assert client.get("/api/draft").json() == {"exists": False}


def test_errors(client):
    assert post(client, "/api/draft/pick", json={"player_id": "x"}).status_code == 404
    created, chosen = create(client)
    assert created.status_code == 200
    again = post(client, "/api/draft", json={
        "name": "Outro", "team_size": 2, "teams": [{"name": "A", "captain_id": chosen[0]}, {"name": "B", "captain_id": chosen[1]}],
        "pool_ids": chosen[2:4]})
    assert again.status_code == 400  # já existe um draft
    assert post(client, "/api/draft/pick", json={"player_id": chosen[0]}).status_code == 400  # capitão
    assert post(client, "/api/draft/pick", json={"player_id": "inexistente"}).status_code == 400


def test_draft_is_public_but_rejects_foreign_origin_and_unknown_players(client):
    foreign = {"Origin": "https://outro-site.example"}
    for method, path in (("post", "/api/draft"), ("post", "/api/draft/pick"),
                         ("post", "/api/draft/undo"), ("delete", "/api/draft")):
        assert getattr(client, method)(path, headers=foreign).status_code == 403
    bad = post(client, "/api/draft", json={"name": "Copa", "team_size": 2,
               "teams": [{"name": "A", "captain_id": "nao-existe"}, {"name": "B", "captain_id": "tambem-nao"}],
               "pool_ids": ["a", "b"]})
    assert bad.status_code == 400 and "ativos" in bad.json()["detail"]


def test_draft_persists_in_sqlite(local_client, local):
    for nick in "ABCDEF":
        local.store.save_player(nick, 3, None, skill_level=5)
    local.invalidate()
    players = [p["id"] for p in local_client.get("/api/players").json()]
    body = {"name": "Local", "team_size": 3, "teams": [{"name": "X", "captain_id": players[0]},
            {"name": "Y", "captain_id": players[1]}], "pool_ids": players[2:6]}
    assert post(local_client, "/api/draft", json=body).status_code == 200
    assert post(local_client, "/api/draft/pick", json={"player_id": players[2]}).status_code == 200
    saved = local.store.draft_get()
    assert saved["picks"][0]["player_id"] == players[2]
