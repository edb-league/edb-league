"""Avisos no Discord: desligados por padrão, sem marcar ninguém e sem atrapalhar o registro."""
from __future__ import annotations

import io

import pytest

from edb_api import notify

from .conftest import ORIGIN
from .test_series_import import bo3_files, commit_body, preview

HOOK = "https://discord.com/api/webhooks/123/abc"


@pytest.fixture
def sent(monkeypatch):
    calls = []
    monkeypatch.setattr(notify, "_background", lambda fn, *args: fn(*args))
    monkeypatch.setattr(notify, "_post", lambda url, payload: calls.append((url, payload)))
    return calls


def save_series(admin):
    item = preview(admin, bo3_files()).json()["series"][0]
    response = admin.post("/api/admin/import/series/commit", json=commit_body(item), headers=ORIGIN)
    assert response.status_code == 200, response.text


def test_nothing_is_sent_without_a_webhook(admin, sent, monkeypatch):
    save_series(admin)
    assert sent == []
    monkeypatch.setenv("EDB_DISCORD_WEBHOOK_URL", "https://exemplo.com/hook")   # não é do Discord: ignorado
    assert notify.webhook() == ""


def test_series_commit_announces_score_and_link_without_pinging_anyone(admin, sent, monkeypatch):
    monkeypatch.setenv("EDB_DISCORD_WEBHOOK_URL", HOOK)
    save_series(admin)
    assert len(sent) == 1
    url, payload = sent[0]
    assert url == HOOK and payload["allowed_mentions"] == {"parse": []}
    text = payload["content"]
    assert "PT 2 x 0 PL (BO3)" in text and "Inferno (13 a 6)" in text and "Mirage (13 a 8)" in text
    assert "/partidas?temporada=1" in text and "votar no MVP" in text
    assert "76561198" not in text   # nenhum SteamID


def test_a_failing_webhook_never_blocks_the_registration(admin, monkeypatch):
    monkeypatch.setenv("EDB_DISCORD_WEBHOOK_URL", HOOK)
    monkeypatch.setattr(notify, "_background", lambda fn, *args: fn(*args))

    def boom(*_args, **_kwargs):
        raise notify.requests.ConnectionError("fora do ar")

    monkeypatch.setattr(notify.requests, "post", boom)
    save_series(admin)   # não levanta


def test_single_match_and_homologation_messages(sent, monkeypatch):
    monkeypatch.setenv("EDB_DISCORD_WEBHOOK_URL", HOOK)
    notify.match_saved("abc", "Inferno", 22)
    notify.season_homologated(1, {"MVP": "Falcão", "Xinxa": "@everyone"})
    first, second = (p["content"] for _, p in sent)
    assert "/partidas/mapa/abc" in first and "Inferno" in first
    assert "Temporada 1 homologada" in second and "MVP: Falcão" in second and "/temporadas" in second
    assert all(p["allowed_mentions"] == {"parse": []} for _, p in sent)
