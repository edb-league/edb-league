"""BO3 upload staging: stable roster, verified order and strict map results."""
from datetime import date
import pytest

from bo3_admin import build_bo3_bundle, roster_for_preview


def sample_staged():
    members=[{"steamid":str(76561197960265728+x),
              "nickname":f"User{x}", "kills":x+10,
              "deaths":5,"assists":3,"damage":1000,
              "rounds":20,"headshots":3,"plants":0,"defuses":0,
              "rating":None,"kast":None,"open_kills":None,"trade_kills":None}
             for x in range(10)]
    return [{"id":f"demo{i}","filename":f"map{i}.dem.gz","map":name,
             "rounds_total":20,"players":[dict(m) for m in members],"warnings":[]}
            for i,name in enumerate(("Mirage","Dust2","Inferno"))]


def test_three_demos_create_one_two_one_bo3_with_thirty_stats():
    s=sample_staged()
    roster=roster_for_preview(s)
    team_a=list(roster)[:5]
    ids={sid:"id-"+sid for sid in roster}
    bundle=build_bo3_bundle(s,[1,0,2],team_a,["a","b","a"],
                            date(2026,10,12),1,ids,replace_old=True)
    assert bundle["season_number"]==0
    assert bundle["sequence_number"]==1
    assert bundle["played_on"]=="2026-10-12"
    assert bundle["replace_old"] is True
    assert [m["id"] for m in bundle["maps"]]==["demo1","demo0","demo2"]
    assert [m["winner_side"] for m in bundle["maps"]]==["a","b","a"]
    assert len(bundle["roster"])==10
    assert [x["team_side"] for x in bundle["roster"]].count("a")==5
    assert len(bundle["stats"])==30
    assert bundle["stats"][0]["observed_nickname"]=="User0"


def test_block_invalid_bo3_before_any_destructive_database_action():
    s=sample_staged()
    roster=roster_for_preview(s)
    team_a=list(roster)[:5]
    ids={sid:"id-"+sid for sid in roster}
    def attempt(order,winners):
        return build_bo3_bundle(s,order,team_a,winners,date(2026,10,12),1,ids,True)
    with pytest.raises(ValueError,match="ordem correta"): attempt([0,0,2],["a","b","a"])
    with pytest.raises(ValueError,match="2 a 1"): attempt([0,1,2],["a","a","a"])
    with pytest.raises(ValueError,match="selecione|cinco|cinco".capitalize().lower()):
        build_bo3_bundle(s,[0,1,2],[],["a","b","a"],
                         date(2026,10,12),1,ids)
    with pytest.raises(ValueError,match="18/10/2026"):
        build_bo3_bundle(s,[0,1,2],team_a,["a","b","a"],
                         date(2026,10,19),1,ids)
    with pytest.raises(ValueError,match="SteamIDs não são idênticos"):
        changed=sample_staged()
        changed[1]["players"][-1]["steamid"]="unknown"
        build_bo3_bundle(changed,[0,1,2],team_a,["a","b","a"],
                         date(2026,10,12),1,ids)


def test_admin_has_transactional_confirmation_not_automatic_delete():
    from pathlib import Path
    app=(Path(__file__).resolve().parents[1]/"app.py").read_text(encoding="utf-8")
    assert "A Temporada 0 está encerrada e bloqueada" in app
    assert "'POST','rpc/ensure_edb_calendar',payload={}" in app
    assert "def ensure_current_calendar(" in app
    assert "rpc/import_edb_bo3_bundle" not in app
    assert "analyze_one_bo3_upload(bo3_file)" not in app
