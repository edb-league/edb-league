"""CS2 regression: preserves combat events when round_end advances round index."""
import sys
import types

import pandas as pd
import pytest

from demo_importer import (
    _trim_outside_rounds, _trim_warmup, _validate_combat_stats, parse_demo,
)


def test_round_number_offset_uses_tick_windows_instead_of_erasing_kills():
    combat=pd.DataFrame({
        "tick":[150,350],"total_rounds_played":[0,1],
        "attacker_steamid":[101,102],"user_steamid":[102,101],
    })
    starts={0:100,1:300}
    ends={1:200,2:400}
    output=_trim_outside_rounds(combat,starts,ends)
    assert output["tick"].tolist()==[150,350]


def test_round_filter_ignores_events_after_round_end():
    combat=pd.DataFrame({
        "tick":[150,245,350,450],
        "total_rounds_played":[0,0,1,2],
    })
    result=_trim_outside_rounds(combat,{0:100,1:300},{1:200,2:400})
    assert result["tick"].tolist()==[150,350]


def test_warmup_flag_overrides_late_match_start_tick():
    data=pd.DataFrame({
        "tick":[50,150,250],
        "is_warmup_period":[True,False,False],
    })
    result=_trim_warmup(data,match_tick=999)
    assert result["tick"].tolist()==[150,250]


def test_no_valid_kills_or_deaths_is_a_hard_failure():
    with pytest.raises(ValueError,match="não foi possível extrair"):
        _validate_combat_stats([{"kills":0,"deaths":0,"rounds":20}],20)
    with pytest.raises(ValueError,match="não foi possível extrair"):
        _validate_combat_stats([{"kills":15,"deaths":0,"rounds":20}],20)


class MockOffsetDemo:
    def __init__(self,path): pass

    def parse_header(self):
        return {"map_name":"de_mirage"}

    def parse_player_info(self):
        return pd.DataFrame([{"steamid":i,"name":f"Player{i}"} for i in range(101,111)])

    def parse_event(self,name,**kwargs):
        warm={"is_warmup_period":False}
        if name=="player_death":
            return pd.DataFrame([
                {"tick":150,"total_rounds_played":0,"attacker_steamid":101,
                 "user_steamid":102,"attacker_name":"Player101","user_name":"Player102",
                 "attacker_team_name":"T","user_team_name":"CT",
                 "headshot":True,**warm},
                {"tick":350,"total_rounds_played":1,"attacker_steamid":102,
                 "user_steamid":101,"attacker_name":"Player102","user_name":"Player101",
                 "attacker_team_name":"CT","user_team_name":"T",
                 "headshot":False,**warm},
            ])
        if name=="player_hurt":
            return pd.DataFrame([
                {"tick":145,"total_rounds_played":0,
                 "attacker_steamid":101,"user_steamid":102,
                 "attacker_name":"Player101","user_name":"Player102",
                 "attacker_team_name":"T","user_team_name":"CT",
                 "dmg_health":55,**warm}
            ])
        if name=="player_spawn":
            return pd.DataFrame([
                {"tick":tick,"total_rounds_played":round_no,
                 "user_steamid":i,"user_name":f"Player{i}",**warm}
                for tick,round_no in ((100,0),(300,1))
                for i in range(101,111)
            ])
        if name=="round_start":
            return pd.DataFrame([
                {"tick":100,"total_rounds_played":0,**warm},
                {"tick":300,"total_rounds_played":1,**warm},
            ])
        if name=="round_end":
            return pd.DataFrame([
                {"tick":200,"total_rounds_played":1,**warm},
                {"tick":400,"total_rounds_played":2,**warm},
            ])
        if name=="round_announce_match_start":
            # This event may happen late; the actual warmup flag is authoritative.
            return pd.DataFrame([{"tick":999}])
        return pd.DataFrame()


def test_full_parser_returns_actual_combat_instead_of_zero_preview(monkeypatch):
    monkeypatch.setitem(sys.modules,"demoparser2",
                        types.SimpleNamespace(DemoParser=MockOffsetDemo))
    result=parse_demo("/fake.dem","example-fingerprint")
    rows={p["steamid"]:p for p in result.players}
    assert result.map_name=="Mirage"
    assert result.rounds_total==2
    assert len(result.players)==10
    assert rows["101"]["kills"]==1
    assert rows["101"]["deaths"]==1
    assert rows["101"]["damage"]==55
    assert rows["102"]["kills"]==1
    assert rows["102"]["deaths"]==1
    assert rows["101"]["headshots"]==1


def test_full_parser_refuses_zero_combat_even_with_ten_players_and_rounds(monkeypatch):
    class NoCombatEvents(MockOffsetDemo):
        def parse_event(self,name,**kwargs):
            if name=="player_death":
                return pd.DataFrame([{
                    "tick":99999,"total_rounds_played":100,
                    "attacker_steamid":101,"user_steamid":102,
                    "is_warmup_period":False,
                }])
            return super().parse_event(name,**kwargs)
    monkeypatch.setitem(sys.modules,"demoparser2",
                        types.SimpleNamespace(DemoParser=NoCombatEvents))
    with pytest.raises(ValueError,match="não foi possível extrair"):
        parse_demo("/fake.dem","fingerprint")
