"""BAGRES: menor ADR em primeiro; Prêmio Henio: pior ADR de carreira."""

from pathlib import Path

import pandas as pd

import pytest

from edb.bagres import bagres_board, premio_henio

ROOT=Path(__file__).resolve().parents[1]

def rows():
    return [
        {"player_id":"a","match_id":"m1","nickname":"Alfa","player_name":"Alfa",
         "damage":800,"rounds":10,"kills":8,"deaths":13,"won":False},
        {"player_id":"a","match_id":"m2","nickname":"Alfa","player_name":"Alfa",
         "damage":1200,"rounds":20,"kills":11,"deaths":17,"won":True},
        {"player_id":"b","match_id":"m1","nickname":"Bravo","player_name":"Bravo",
         "damage":900,"rounds":10,"kills":12,"deaths":8,"won":True},
        {"player_id":"b","match_id":"m2","nickname":"Bravo","player_name":"Bravo",
         "damage":2400,"rounds":20,"kills":22,"deaths":13,"won":True},
        {"player_id":"c","match_id":"m2","nickname":"Charlie","player_name":"Charlie",
         "damage":500,"rounds":10,"kills":6,"deaths":15,"won":False},
        {"player_id":"d","match_id":"m2","nickname":"Delta","player_name":"Delta",
         "damage":None,"rounds":20,"kills":10,"deaths":14,"won":False},
    ]

def test_bagres_uses_weighted_adr_ascending_not_simple_game_average():
    board=bagres_board(pd.DataFrame(rows()),{"a":2,"b":8,"c":5,"d":4})
    assert list(board["Jogador"])==["Charlie","Alfa","Bravo"]
    assert list(board["ADR"])==[50.0,66.7,110.0]
    assert list(board["Nível"])==[5,2,8]
    assert list(board["Elegível"])==[False,True,True]
    assert board.iloc[1]["Partidas"]==2
    assert board.iloc[1]["Kills"]==19
    assert board.iloc[1]["Vitórias"]==1

def test_bagres_excludes_partial_measurements_and_duplicates():
    data=rows()
    data.insert(1,dict(data[0]))
    board=bagres_board(pd.DataFrame(data))
    assert board.loc[board["Jogador"]=="Alfa","Partidas"].iloc[0]==2
    data.append({"player_id":"b","match_id":"m3","nickname":"Bravo",
                 "damage":None,"rounds":20,"kills":3,"deaths":4,"won":False})
    board=bagres_board(pd.DataFrame(data))
    assert "Bravo" not in set(board["Jogador"])
    assert bagres_board(pd.DataFrame()).empty

def test_premio_henio_requires_two_maps_and_uses_all_time_adr():
    assert premio_henio(rows())["holders"]==[{"id":"a","name":"Alfa","maps":2}]
    assert premio_henio(rows())["adr"]==pytest.approx(2000/30)
    assert premio_henio(rows(),min_maps=3) is None
    assert premio_henio(rows()[-2:]) is None

def test_premio_henio_exact_ties_are_shared():
    data=rows()
    for row in data:
        if row["player_id"]=="b":
            row["damage"]=800 if row["match_id"]=="m1" else 1200
    award=premio_henio(data)
    assert {h["id"] for h in award["holders"]}=={"a","b"}
