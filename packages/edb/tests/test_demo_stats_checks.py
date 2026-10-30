"""Conferências do demo_stats numa demo sintética: reinício de round, jogador que saiu, partida incompleta."""
import sys
from types import SimpleNamespace

import pandas as pd
import pytest

from edb import demo_stats

A = [str(76561198000000100 + i) for i in range(5)]   # começam de T
B = [str(76561198000000200 + i) for i in range(5)]   # começam de CT
NICK = {sid: f"A{i}" for i, sid in enumerate(A)} | {sid: f"B{i}" for i, sid in enumerate(B)}


class Demo:
    """Monta os eventos de uma partida em que o time A vence todos os rounds."""

    def __init__(self, rounds=13, extra_start=None, leaver=None, begins=(100,), triple_round=None, plants=(), defuses=(),
                 reason=None):
        self.rounds, self.extra_start, self.leaver, self.begins = rounds, extra_start, leaver, begins
        self.triple_round, self.plants, self.defuses, self.reason = triple_round, plants, defuses, reason
        self.events = self._build()

    def _build(self):
        deaths, hurts, fires, starts, freezes, ends = [], [], [], [], [], []
        for r in range(1, self.rounds + 1):
            base = 1000 * r
            a_team, b_team = (2, 3) if r <= 12 else (3, 2)
            starts.append(base)
            freezes.append(base + 100)
            ends.append({"tick": base + 800, "winner": "T" if a_team == 2 else "CT"}
                        | ({"reason": self.reason} if self.reason else {}))
            for sid in A + B:
                if self.leaver and sid == self.leaver[0] and r >= self.leaver[1]:
                    continue
                fires.append({"tick": base + 200, "user_steamid": sid, "weapon": "weapon_ak47"})
            victims = [0, 1, 2] if r == self.triple_round else [r % 4]
            for n, v in enumerate(victims):
                a, b, tick = A[(r + n) % 5], B[v], base + 300 + 20 * n
                deaths.append({
                    "tick": tick, "attacker_steamid": a, "user_steamid": b, "assister_steamid": "0",
                    "attacker_team_num": a_team, "user_team_num": b_team, "attacker_name": NICK[a],
                    "user_name": NICK[b], "weapon": "ak47", "headshot": True, "thrusmoke": False,
                    "noscope": False, "penetrated": False, "attackerblind": False, "assistedflash": False,
                    "is_warmup_period": False})
                hurts.append({
                    "tick": tick, "attacker_steamid": a, "user_steamid": b, "attacker_team_num": a_team,
                    "user_team_num": b_team, "dmg_health": 100, "health": 0, "weapon": "ak47",
                    "is_warmup_period": False})
        if self.extra_start:
            starts.append(self.extra_start)
        blind = [{"tick": 1250, "attacker_steamid": A[0], "user_steamid": B[0], "attacker_team_num": 2,
                  "user_team_num": 3, "blind_duration": 1.0, "is_warmup_period": False}]
        frame = pd.DataFrame
        # Plant é do time T do round (A até o 12, B depois); desarme é do CT.
        plants = frame({"tick": [1000 * r + 500 for r in self.plants], "is_warmup_period": False,
                        "user_steamid": [A[0] if r <= 12 else B[0] for r in self.plants]})
        defuses = frame({"tick": [1000 * r + 700 for r in self.defuses], "is_warmup_period": False,
                         "user_steamid": [B[0] if r <= 12 else A[0] for r in self.defuses]})
        return {
            "bomb_planted": plants, "bomb_defused": defuses,
            "begin_new_match": frame({"tick": list(self.begins)}),
            "round_start": frame({"tick": starts}),
            "round_freeze_end": frame({"tick": freezes}),
            "round_end": frame(ends).assign(is_warmup_period=False),
            "player_death": frame(deaths), "player_hurt": frame(hurts), "weapon_fire": frame(fires),
            "player_blind": frame(blind),
        }

    def install(self, monkeypatch):
        outer = self

        class Parser:
            def __init__(self, path):
                pass

            def parse_header(self):
                return {"map_name": "de_inferno", "server_name": "XPLAY.GG"}

            def parse_events(self, names, player=None, other=None):
                return [(n, outer.events[n]) for n in names if n in outer.events]

            def parse_ticks(self, props, ticks=None):
                rows = [{"steamid": s, "team_num": 2, "name": NICK[s]} for s in A]
                rows += [{"steamid": s, "team_num": 3, "name": NICK[s]} for s in B]
                return pd.DataFrame(rows)

        monkeypatch.setitem(sys.modules, "demoparser2", SimpleNamespace(DemoParser=Parser))


def run(monkeypatch, **options):
    Demo(**options).install(monkeypatch)
    return demo_stats.analyze("fake.dem")


def player(result, sid):
    return next(p for p in result["players"] if p["steamid"] == sid)


def test_clean_match_has_no_warnings_and_closes_its_accounts(monkeypatch):
    result = run(monkeypatch)
    assert result["rounds"] == 13 and result["score"] == {"team_t_first": 13, "team_ct_first": 0}
    assert result["warnings"] == []
    assert sum(p["open_kills"] for p in result["players"]) == 13
    assert all(p["rounds"] == 13 and p["rounds_t"] + p["rounds_ct"] == 13 for p in result["players"])
    assert sum(p["kills"] for p in result["players"]) == 13


def test_restarted_round_does_not_shift_the_following_rounds(monkeypatch):
    result = run(monkeypatch, extra_start=4900)   # round_start abortado entre o round 4 e o 5
    assert sum(p["open_kills"] for p in result["players"]) == 13
    assert result["score"]["team_t_first"] == 13
    assert any("reinício" in w for w in result["warnings"])


def test_player_who_left_keeps_only_the_rounds_he_played(monkeypatch):
    result = run(monkeypatch, leaver=(B[4], 3))
    gone = player(result, B[4])
    assert gone["rounds"] == 2 and gone["rounds_t"] + gone["rounds_ct"] == 2
    assert gone["kast"] <= 100
    assert player(result, B[0])["rounds"] == 13
    warning = next(w for w in result["warnings"] if "B4" in w)
    assert "depois do round 2" in warning


def test_leaver_is_not_counted_as_alive_for_clutches(monkeypatch):
    # No round 5 caem B0, B1 e B2. Com o B4 fora, o B3 fica sozinho (1v5); contando o B4, ninguém ficaria sozinho.
    result = run(monkeypatch, leaver=(B[4], 3), triple_round=5)
    assert player(result, B[3])["last_alive_rounds"] == 1
    assert player(result, B[3])["clutches"]["1v5"] == [1, 0]


def test_incomplete_match_and_restart_are_reported(monkeypatch):
    result = run(monkeypatch, rounds=9, begins=(50, 100))
    assert any("não fecha uma partida" in w for w in result["warnings"])
    assert any("reiniciou 1 vez" in w for w in result["warnings"])


@pytest.mark.parametrize("score,rounds,expected", [
    ({2: 13, 3: 0}, 13, True), ({2: 13, 3: 11}, 24, True), ({2: 12, 3: 11}, 23, False),
    ({2: 14, 3: 10}, 24, False), ({2: 16, 3: 14}, 30, True), ({2: 15, 3: 15}, 30, False),
])
def test_finished_rule(score, rounds, expected):
    assert demo_stats._finished(score, rounds) is expected


def test_absences_only_count_long_gaps():
    assert demo_stats._absences({1, 2, 7, 8}, 8) == [(3, 6)] and demo_stats._absences({1, 2, 6, 7}, 7) == []
    assert demo_stats._absences({1, 2}, 8) == [(3, 8)] and demo_stats._absences({5, 6, 7, 8, 9}, 9) == [(1, 4)]


def test_timeline_has_one_entry_per_round_with_running_score_and_sides(monkeypatch):
    result = run(monkeypatch, rounds=14)
    timeline = result["timeline"]
    assert [r["round"] for r in timeline] == list(range(1, 15))
    assert timeline[0]["score"] == [1, 0] and timeline[-1]["score"] == [14, 0]
    assert all(r["winner"] == "t_first" for r in timeline)
    # O time A começa de T e troca de lado depois do round 12.
    assert {r["side"] for r in timeline[:12]} == {"t"} and {r["side"] for r in timeline[12:]} == {"ct"}


def test_timeline_reasons_come_from_bomb_events(monkeypatch):
    # Rounds 1-12 são vitórias de T; 13-14 de CT. Plant no 2; plant e desarme no 13.
    timeline = run(monkeypatch, rounds=14, plants=(2, 13), defuses=(13,))["timeline"]
    by_round = {r["round"]: r for r in timeline}
    assert by_round[1]["reason"] == "eliminacao" and by_round[1]["planted"] is False
    assert by_round[2]["reason"] == "bomba" and by_round[2]["planted"] is True
    assert by_round[13]["reason"] == "desarme" and by_round[13]["planted"] is True
    assert by_round[14]["reason"] is None   # CT sem bomba e sem motivo informado: não chuta entre eliminação e tempo


def test_timeline_uses_the_game_reason_only_to_break_ties(monkeypatch):
    assert run(monkeypatch, rounds=14, reason="ct_win")["timeline"][13]["reason"] == "eliminacao"
    assert run(monkeypatch, rounds=14, reason="target_saved")["timeline"][13]["reason"] == "tempo"
    # T com a bomba plantada, mas o jogo diz que foi eliminação: vale a eliminação.
    assert run(monkeypatch, rounds=14, plants=(2,), reason="t_win")["timeline"][1]["reason"] == "eliminacao"
