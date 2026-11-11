"""Motor do draft de campeonato (capitães escolhendo em turnos)."""
import pytest

from edb import draft

NOW = "2026-11-11T12:00:00+00:00"


def teams(n):
    return [{"name": f"Time {i}", "captain_id": f"c{i}"} for i in range(1, n + 1)]


def pool(n, size):
    return [f"p{i}" for i in range(n * (size - 1))]


def make(n=4, size=5, snake=True):
    return draft.create_draft("Copa", size, teams(n), pool(n, size), NOW, snake=snake)


def test_snake_sequence():
    assert draft.pick_sequence(4, 3) == [1, 2, 3, 4, 4, 3, 2, 1]
    assert draft.pick_sequence(3, 4, snake=False) == [1, 2, 3] * 3
    assert len(draft.pick_sequence(4, 5)) == 16


def test_full_draft_snake_order_and_undo():
    state = make(2, 3)
    expected = [1, 2, 2, 1]
    for i, team in enumerate(expected):
        assert draft.next_pick(state)["team"] == team
        state = draft.apply_pick(state, f"p{i}", NOW)
    assert state["status"] == "done" and draft.next_pick(state) is None
    assert state["teams"][0]["picks"] == ["p0", "p3"] and state["teams"][1]["picks"] == ["p1", "p2"]
    state = draft.undo_pick(state, NOW)
    assert state["status"] == "drafting" and draft.next_pick(state) == {"number": 4, "total": 4, "team": 1}
    assert "p3" in draft.available(state) and state["teams"][0]["picks"] == ["p0"]


def test_pick_validation():
    state = make(2, 3)
    with pytest.raises(ValueError, match="disponível"):
        draft.apply_pick(state, "c1", NOW)  # capitão não é escolhível
    state = draft.apply_pick(state, "p0", NOW)
    with pytest.raises(ValueError, match="disponível"):
        draft.apply_pick(state, "p0", NOW)  # já escolhido
    with pytest.raises(ValueError, match="desfazer"):
        draft.undo_pick(make(2, 3), NOW)


def test_create_validation():
    with pytest.raises(ValueError, match="nome"):
        draft.create_draft("  ", 5, teams(4), pool(4, 5), NOW)
    with pytest.raises(ValueError, match="selecione 16"):
        draft.create_draft("Copa", 5, teams(4), pool(4, 5)[:-1], NOW)
    with pytest.raises(ValueError, match="capitães"):
        draft.create_draft("Copa", 2, teams(2), ["c1", "x"], NOW)
    with pytest.raises(ValueError, match="repetidos"):
        draft.create_draft("Copa", 2, teams(2), ["x", "x"], NOW)
    dup = teams(2)
    dup[1]["captain_id"] = "c1"
    with pytest.raises(ValueError, match="capitão de dois"):
        draft.create_draft("Copa", 2, dup, ["x", "y"], NOW)
    same = teams(2)
    same[1]["name"] = "time 1"
    with pytest.raises(ValueError, match="mesmo nome"):
        draft.create_draft("Copa", 2, same, ["x", "y"], NOW)
    with pytest.raises(ValueError, match="2 a 8"):
        draft.create_draft("Copa", 2, teams(1), [], NOW)
