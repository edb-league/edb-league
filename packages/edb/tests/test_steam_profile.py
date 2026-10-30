"""Aba Jogadores: SteamID, foto, horas de CS e banner com estatísticas."""

from pathlib import Path

import requests

from edb.steam_profile import (
    SteamUnavailable, fetch_steam_profile, normalize_steamid64,
    safe_avatar_url, steam_view,
)

ROOT = Path(__file__).resolve().parents[1]

KEY = "CHAVE-SECRETA-123"

class _Reply:
    def __init__(self, payload=None, error=None):
        self.payload, self.error = payload, error

    def raise_for_status(self):
        if self.error:
            raise self.error

    def json(self):
        return self.payload

class _Session:
    def __init__(self, summary, owned):
        self.summary, self.owned, self.calls = summary, owned, []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params))
        return self.summary if "GetPlayerSummaries" in url else self.owned

def _profile(avatar="https://avatars.steamstatic.com/abc_full.jpg"):
    return _Reply({"response": {"players": [{"personaname": "Kvra", "avatarfull": avatar}]}})

def test_steamid_formats_are_converted_and_junk_rejected():
    assert normalize_steamid64("76561198000000001") == "76561198000000001"
    assert normalize_steamid64(" STEAM_0:1:12345 ") == "76561197960290419"
    assert normalize_steamid64("[U:1:24691]") == "76561197960290419"
    assert normalize_steamid64("U:1:24691") == "76561197960290419"
    for bad in ("", None, "abc", "12345", "76561198000000", "STEAM_0:2:1", "[U:1:0]"):
        assert normalize_steamid64(bad) is None

def test_avatar_must_come_from_steam_over_https():
    assert safe_avatar_url("https://avatars.steamstatic.com/a.jpg")
    assert safe_avatar_url("https://avatars.akamai.steamstatic.com/a.jpg")
    assert safe_avatar_url("http://avatars.steamstatic.com/a.jpg") == ""
    assert safe_avatar_url("https://evil.example.com/steamstatic.com/a.jpg") == ""
    assert safe_avatar_url("javascript:alert(1)") == ""
    assert safe_avatar_url(None) == ""

def test_fetch_reads_avatar_name_and_cs_hours_in_hours():
    owned = _Reply({"response": {"games": [{"appid": 730, "playtime_forever": 7380}]}})
    session = _Session(_profile(), owned)
    data = fetch_steam_profile("76561198000000001", KEY, session=session)
    assert data == {"found": True, "persona": "Kvra", "hours": 123.0, "hours_visible": True,
                    "avatar": "https://avatars.steamstatic.com/abc_full.jpg"}
    assert session.calls[1][1]["appids_filter[0]"] == 730
    assert session.calls[1][1]["include_played_free_games"] == 1

def test_private_game_details_keep_the_avatar_but_hide_hours():
    session = _Session(_profile(), _Reply({"response": {}}))
    data = fetch_steam_profile("76561198000000001", KEY, session=session)
    assert data["hours"] is None and data["hours_visible"] is False
    assert data["avatar"].startswith("https://avatars.steamstatic.com/")

def test_network_errors_never_leak_the_key():
    boom = requests.ConnectionError("falhou em https://api.steampowered.com/?key=" + KEY)
    session = _Session(_Reply(error=boom), _Reply({}))
    try:
        fetch_steam_profile("76561198000000001", KEY, session=session)
    except SteamUnavailable as exc:
        assert KEY not in str(exc) and exc.__cause__ is None
    else:
        raise AssertionError("deveria falhar")
    bad_json = _Session(_Reply(ValueError("x") and None), _Reply({}))
    bad_json.summary.json = lambda: (_ for _ in ()).throw(ValueError("json"))
    try:
        fetch_steam_profile("76561198000000001", KEY, session=bad_json)
    except SteamUnavailable:
        pass
    else:
        raise AssertionError("JSON inválido deveria falhar")

def test_steam_view_states():
    ok = lambda sid, key: {"persona": "Kvra", "avatar": "https://avatars.steamstatic.com/a.jpg",
                           "hours": 1234.0, "hours_visible": True}
    private = lambda sid, key: {"persona": "Kvra", "avatar": "", "hours": None, "hours_visible": False}

    def down(sid, key):
        raise SteamUnavailable("x")

    unlinked = steam_view("", KEY, ok)
    assert unlinked["state"] == "unlinked" and unlinked["hours"] == 0.0 and unlinked["avatar"] == ""
    assert steam_view(None, KEY, ok)["hours"] == 0.0
    assert steam_view("lixo", KEY, ok)["state"] == "invalid"
    assert steam_view("lixo", KEY, ok)["hours"] == 0.0
    nokey = steam_view("76561198000000001", "", ok)
    assert nokey["state"] == "no_key" and nokey["hours"] is None and nokey["note"]
    linked = steam_view("76561198000000001", KEY, ok)
    assert linked["state"] == "linked" and linked["hours"] == 1234.0 and linked["persona"] == "Kvra"
    hidden = steam_view("76561198000000001", KEY, private)
    assert hidden["hours"] is None and "não públicas" in hidden["note"]
    assert steam_view("76561198000000001", KEY, down)["state"] == "error"

SUMMARY = {"games": 5, "wins": 3, "win_rate": 60.0, "kills": 82, "deaths": 70,
           "assists": 20, "kd": 1.1714, "adr": 78.46}

def _http_error(status):
    return requests.HTTPError("erro", response=type("R", (), {"status_code": status})())

def test_failures_carry_a_safe_reason_and_a_clear_note():
    cases = {403: "key", 401: "key", 429: "limit", 500: "http"}
    for status, reason in cases.items():
        session = _Session(_Reply(error=_http_error(status)), _Reply({}))
        try:
            fetch_steam_profile("76561198000000001", KEY, session=session)
        except SteamUnavailable as exc:
            assert exc.reason == reason and KEY not in str(exc)
        else:
            raise AssertionError("deveria falhar")
    timeout = _Session(_Reply(error=requests.Timeout("lento")), _Reply({}))
    try:
        fetch_steam_profile("76561198000000001", KEY, session=timeout)
    except SteamUnavailable as exc:
        assert exc.reason == "timeout"

    def refused(sid, key):
        raise SteamUnavailable("key")

    def limited(sid, key):
        raise SteamUnavailable("limit")

    assert "recusada" in steam_view("76561198000000001", KEY, refused)["note"]
    assert "limitou" in steam_view("76561198000000001", KEY, limited)["note"]

def test_missing_profile_is_reported_and_key_is_cleaned():
    gone = _Session(_Reply({"response": {"players": []}}), _Reply({"response": {}}))
    data = fetch_steam_profile("76561198000000001", KEY, session=gone)
    assert data["found"] is False
    view = steam_view("76561198000000001", KEY, lambda sid, key: data)
    assert view["state"] == "notfound" and "SteamID" in view["note"]
    seen = []

    def spy(sid, key):
        seen.append(key)
        return {"found": True, "persona": "", "avatar": "", "hours": 1.0, "hours_visible": True}

    steam_view("76561198000000001", ' "abc123" \n', spy)
    steam_view("76561198000000001", "  'abc123'", spy)
    assert seen == ["abc123", "abc123"]
    assert steam_view("76561198000000001", "  ", spy)["state"] == "no_key"

def test_fetch_steam_avatars_batches_and_filters_hosts():
    from edb.steam_profile import fetch_steam_avatars

    calls = []

    class Response:
        def __init__(self, players):
            self._players = players

        def raise_for_status(self):
            pass

        def json(self):
            return {"response": {"players": self._players}}

    class Session:
        def get(self, url, params=None, timeout=None):
            calls.append(params["steamids"].split(","))
            players = [{"steamid": s, "avatarfull": f"https://avatars.steamstatic.com/{s}.jpg"} for s in calls[-1]]
            players.append({"steamid": "evil", "avatarfull": "https://evil.example.com/x.jpg"})
            return Response(players)

    ids = [str(76561198000000000 + i) for i in range(150)]
    found = fetch_steam_avatars(ids, "chave", session=Session())
    assert [len(c) for c in calls] == [100, 50]  # a Steam aceita 100 ids por chamada
    assert len(found) == 150 and "evil" not in found
    assert found[ids[0]].startswith("https://avatars.steamstatic.com/")
