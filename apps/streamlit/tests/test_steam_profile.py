"""Aba Jogadores: SteamID, foto, horas de CS e banner com estatísticas."""
from pathlib import Path

import requests

from player_page import PLAYER_CSS, SILHOUETTE, format_hours, player_banner
from edb.steam_profile import (
    SteamUnavailable, fetch_steam_profile, normalize_steamid64,
    safe_avatar_url, steam_view,
)
from top_navigation import NAV_ITEMS, ROUTES, top_navigation

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.py").read_text(encoding="utf-8")
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


def test_banner_unlinked_shows_gray_silhouette_and_zero_hours():
    html = player_banner("Pyetev", steam_view("", KEY, None), SUMMARY)
    assert SILHOUETTE.split(",", 1)[0] == "data:image/svg+xml;utf8"
    assert 'src="' + SILHOUETTE.replace('"', "&quot;") in html or SILHOUETTE in html
    assert "<strong>0 h</strong><span>HORAS DE CS</span>" in html
    assert '<div class="edb-player-persona">' not in html


def test_banner_linked_shows_photo_hours_and_stats_below():
    steam = {"state": "linked", "avatar": "https://avatars.steamstatic.com/a.jpg",
             "persona": "Kvra <b>", "hours": 1234.0, "note": ""}
    html = player_banner("Kvra (Caveira)", steam, SUMMARY)
    assert 'src="https://avatars.steamstatic.com/a.jpg"' in html
    assert "1 234 h" in html and "Steam: Kvra &lt;b&gt;" in html
    body = html[html.index("<section"):]
    assert body.index('class="edb-player-head"') < body.index("HORAS DE CS") < body.index('class="edb-player-stats"')
    assert body.index("<img") < body.index("HORAS DE CS")
    for text in ("<b>5</b><span>Partidas</span>", "<b>3</b><span>Vitórias</span>",
                 "<b>60%</b><span>Aproveitamento</span>", "<b>82</b><span>Kills</span>",
                 "<b>70</b><span>Mortes</span>", "<b>20</b><span>Assistências</span>",
                 "<b>1.17</b><span>K/D</span>", "<b>78.5</b><span>ADR</span>"):
        assert text in html
    assert PLAYER_CSS.count("{") == PLAYER_CSS.count("}")


def test_banner_handles_player_without_matches_and_unavailable_hours():
    empty = {"games": 0, "wins": 0, "win_rate": None, "kills": 0, "deaths": 0,
             "assists": 0, "kd": None, "adr": None}
    steam = steam_view("76561198000000001", "", None)
    html = player_banner("Novato", steam, empty)
    assert "<strong>—</strong>" in html and "Steam ainda não conectada ao site" in html
    assert "<b>–</b><span>Kills</span>" in html and "<b>–</b><span>K/D</span>" in html
    assert "<b>0</b><span>Partidas</span>" in html
    assert format_hours(0.0) == "0 h" and format_hours(5.5) == "5.5 h"
    assert format_hours(None) == "—"


def test_menu_lists_jogadores_right_below_partidas():
    names = [item[1] for item in NAV_ITEMS]
    assert names.index("Jogadores") == names.index("Partidas") + 1
    assert ROUTES["players"] == "Jogadores"
    markup = top_navigation("Jogadores")
    assert 'href="?page=players"' in markup
    assert 'aria-label="Jogadores" aria-current="page"' in markup
    assert markup.index('aria-label="Partidas"') < markup.index('aria-label="Jogadores"') < markup.index('aria-label="Comparar jogadores"')


def test_page_wiring_uses_secret_cache_and_simple_layout():
    page = APP.split("elif page=='Jogadores':", 1)[1].split("elif page=='Hall da Fama':", 1)[0]
    assert page.index("st.selectbox(") < page.index("player_banner(")
    assert "steam_api_key()" in page and "cached_steam_profile" in page
    assert APP.count("STEAM_API_KEY") == 2  # só os nomes dos segredos, nunca o valor
    assert "def cached_steam_profile(steamid64: str, _api_key: str):" in APP
    assert "@st.cache_data(ttl=21600, max_entries=64, show_spinner=False)\ndef cached_steam_profile" in APP
    assert "render_player_profile" not in APP


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


def _load_steam_api_key(secrets_top, secrets_tree):
    import ast
    tree = ast.parse(APP)
    func = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "steam_api_key")
    fake_st = type("St", (), {"secrets": secrets_tree})()
    namespace = {"st": fake_st, "secret": lambda name: secrets_top.get(name, "")}
    exec(compile(ast.Module([func], []), "app.py", "exec"), namespace)
    return namespace["steam_api_key"]


def test_key_is_found_at_top_level_or_inside_a_toml_section():
    top = _load_steam_api_key({"STEAM_API_KEY": "abc"}, {})
    assert top() == "abc"
    nested = _load_steam_api_key({}, {"supabase": {"URL": "x"}, "outra": {"STEAM_API_KEY": "xyz"}})
    assert nested() == "xyz"
    assert _load_steam_api_key({}, {"supabase": {"URL": "x"}, "TOKEN": "t"})() == ""
    assert _load_steam_api_key({}, {})() == ""

    class Broken:
        def values(self):
            raise FileNotFoundError("sem secrets")

    assert _load_steam_api_key({}, Broken())() == ""


def test_no_steam_key_is_ever_committed_to_the_project():
    import re
    files = (
        ROOT / "app.py",
        ROOT.parents[1] / "packages" / "edb" / "edb" / "steam_profile.py",
        ROOT / "player_page.py",
        ROOT / "tests" / "test_steam_profile.py",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"\b[0-9A-Fa-f]{32}\b", text), path.name


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
