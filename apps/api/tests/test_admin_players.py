from __future__ import annotations

from .conftest import ORIGIN
from .ts_contract import check


def post(client, path, **kwargs):
    return client.post(path, headers=ORIGIN, **kwargs)


def patch(client, path, **kwargs):
    return client.patch(path, headers=ORIGIN, **kwargs)


def exercise_crud(client):
    created = post(client, "/api/admin/players", json={"nickname": "Novato", "steamid": "76561198000000999", "skill_level": 7})
    assert created.status_code == 200, created.text
    player = created.json()
    check(player, "AdminPlayer")
    assert player["nickname"] == "Novato" and player["level"] == 7 and player["stars"] == 3
    assert player["steamid"] == "76561198000000999" and player["is_active"] is True
    pid = player["id"]

    public = client.get("/api/players").json()
    assert any(p["id"] == pid for p in public)
    assert not any("steamid" in p for p in public)

    changed = patch(client, f"/api/admin/players/{pid}", json={"skill_level": 9, "nickname": "Novato2"})
    assert changed.status_code == 200 and changed.json()["level"] == 9 and changed.json()["nickname"] == "Novato2"
    assert changed.json()["steamid"] == "76561198000000999"

    archived = post(client, f"/api/admin/players/{pid}/archive")
    assert archived.status_code == 200 and archived.json()["is_active"] is False
    assert not any(p["id"] == pid for p in client.get("/api/players").json())
    assert any(p["id"] == pid for p in client.get("/api/players?include_inactive=true").json())

    back = post(client, f"/api/admin/players/{pid}/reactivate")
    assert back.status_code == 200 and back.json()["is_active"] is True
    overview = client.get("/api/admin/overview").json()
    assert any(p["id"] == pid for p in overview["players"])


def test_player_crud_in_demo(admin):
    before = len(admin.get("/api/players").json())
    exercise_crud(admin)
    assert len(admin.get("/api/players").json()) == before + 1


def test_player_crud_with_temporary_sqlite(local_admin):
    exercise_crud(local_admin)


def test_player_validation_and_missing_ids(admin):
    assert post(admin, "/api/admin/players", json={"nickname": "  ", "skill_level": 5}).status_code in (400, 422)
    assert post(admin, "/api/admin/players", json={"nickname": "X", "skill_level": 11}).status_code == 422
    assert post(admin, "/api/admin/players", json={"skill_level": 5}).status_code == 422
    assert patch(admin, "/api/admin/players/nao-existe", json={"skill_level": 5}).status_code == 404
    assert post(admin, "/api/admin/players/nao-existe/archive").status_code == 404
    assert post(admin, "/api/admin/players/nao-existe/reactivate").status_code == 404
    response = post(admin, "/api/admin/players", json={"nickname": "Falcão", "skill_level": 5})
    assert response.status_code == 200  # nick existente atualiza o cadastro, como no Streamlit


def test_existing_stars_are_kept_when_editing(admin):
    players = admin.get("/api/admin/overview").json()["players"]
    target = next(p for p in players if p["stars"] == 5)
    result = patch(admin, f"/api/admin/players/{target['id']}", json={"skill_level": 2})
    assert result.json()["stars"] == 5 and result.json()["level"] == 2


def test_overview_shape_demo(admin):
    data = admin.get("/api/admin/overview").json()
    check(data, "AdminOverview")
    assert data["cloud"] is True and len(data["players"]) == 14
    assert [s["number"] for s in data["open_seasons"]] == [1, 2]
    assert data["pending_seasons"] == []


def test_overview_shape_local(local_admin):
    local = local_admin.get("/api/admin/overview").json()
    check(local, "AdminOverview")
    assert local["cloud"] is False and local["open_seasons"] == [] and local["pending_seasons"] == []
