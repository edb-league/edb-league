"""Temporadas mensais ancoradas no dia 19, inclusive virada de ano."""
from datetime import date, timedelta

import pandas as pd
import pytest

from season_system import (
    season_dates, season_bar, current_season_number, chosen_season_number,
)
from season_rankings import season_boards


@pytest.mark.parametrize("number,begin,finish",[
    (1,date(2026,10,19),date(2026,11,18)),
    (2,date(2026,11,19),date(2026,12,18)),
    (3,date(2026,12,19),date(2027,1,18)),
    (4,date(2027,1,19),date(2027,2,18)),
    (5,date(2027,2,19),date(2027,3,18)),
    (17,date(2028,2,19),date(2028,3,18)),  # Ano bissexto: 29 dias
])
def test_monthly_period(number,begin,finish):
    assert season_dates(number)==(begin,finish)
    assert finish+timedelta(days=1)==season_dates(number+1)[0]


def test_no_legacy_season_zero_month_start():
    with pytest.raises(ValueError):
        season_dates(0)


def _seasons():
    return [
        {"number":n,"label":f"Temporada {n}",
         "starts_on":season_dates(n)[0].isoformat(),
         "ends_on":season_dates(n)[1].isoformat()}
        for n in range(1,6)
    ]


def test_november_18_still_season_one_november_19_activates_two():
    s=_seasons()
    assert current_season_number(s,date(2026,11,18))==1
    assert current_season_number(s,date(2026,11,19))==2
    assert current_season_number(s,date(2026,12,18))==2
    assert current_season_number(s,date(2026,12,19))==3
    assert chosen_season_number(s,date(2026,11,19),"1")==1


def test_monthly_progress_shows_real_days_left():
    s=_seasons()
    first=season_bar(s,1,"home",3,on_date=date(2026,10,19))
    assert "Dia 1/31" in first
    assert "30 dias restantes" in first
    assert "Dia 1 de 31" in first
    last=season_bar(s,1,"home",3,on_date=date(2026,11,18))
    assert "Dia 31/31" in last and "0 dias restantes" in last
    feb=season_bar(s,5,"home",0,on_date=date(2027,2,19))
    assert "Dia 1/28" in feb


def test_five_xp_weekly_missions_possible_during_long_month():
    played_dates=[
        "2026-10-19","2026-10-26","2026-11-02",
        "2026-11-09","2026-11-16","2026-11-18"
    ]
    frame=pd.DataFrame([
        {"player_id":"P","nickname":"P","stars":3,"match_id":f"week-{i}",
         "played_at":pd.Timestamp(day),"kills":20,"deaths":10,"assists":0,
         "damage":1800,"rounds":20,"won":True}
        for i,day in enumerate(played_dates)
    ])
    ranked=season_boards(frame,1)["xp"].iloc[0]
    assert ranked["Elegível"]
    assert len(ranked["Mapas selecionados"])==6
    assert ranked["XP"]==6*60+5*100
