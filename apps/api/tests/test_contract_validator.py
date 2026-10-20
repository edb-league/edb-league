import pytest

from .ts_contract import Mismatch, check


def test_validator_rejects_wrong_shapes():
    with pytest.raises(Mismatch):
        check({"ok": True}, "Meta")
    with pytest.raises(Mismatch):
        check({"id": "1", "name": "x", "extra": 1}, "PlayerRef")
    with pytest.raises(Mismatch):
        check({"id": 1, "name": "x"}, "PlayerRef")
    with pytest.raises(Mismatch):
        check({"id": "1", "name": None}, "PlayerRef")
    check({"id": "1", "name": "x"}, "PlayerRef")
