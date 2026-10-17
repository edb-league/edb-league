from pathlib import Path
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from storage import Store
from core import enrich,leaderboard,cap_weekly,historical_progress,weekly_awards


def fixture():
    folder=tempfile.TemporaryDirectory()
    db=Store(db_file=Path(folder.name)/'test.db')
    a=db.save_player('XINXA_A',1)
    b=db.save_player('XINXA_B',5)
    for i in range(6):
        mid=f'match_{i:02}'
        db.save_match({'id':mid,'played_at':f'2026-10-{10+i:02}',
                       'map_name':'Inferno','source':'fixture','rounds_total':17,'notes':''},[
            {'match_id':mid,'player_id':a,'kills':7+i,'deaths':10,'assists':2,
             'damage':700,'rounds':17,'won':bool(i%2),'headshots':0,'plants':0,'defuses':0,
             'rating':None,'kast':None,'open_kills':None,'trade_kills':None},
            {'match_id':mid,'player_id':b,'kills':19,'deaths':8,'assists':3,
             'damage':1600,'rounds':17,'won':not bool(i%2),'headshots':0,'plants':0,'defuses':0,
             'rating':None,'kast':None,'open_kills':None,'trade_kills':None}
        ])
    return folder, db, a,b


def test_database_and_rules():
    folder,db,a,b=fixture()
    try:
        f=enrich(db.players(),db.matches(),db.stats())
        assert len(f)==12
        assert db.match_exists('match_00')
        assert not db.match_exists('missing')
        ranked=leaderboard(f)
        assert ranked['Kills'].sum() == 57+114  # duas semanas, nenhuma excede quatro partidas
        assert ranked['XP'].min()>0
        assert len(historical_progress(f))==2
        assert weekly_awards(f)
        assert set(ranked['Jogador']) == {'XINXA_A','XINXA_B'}
    finally:folder.cleanup()


def test_stars_update_and_duplicate():
    folder,db,a,b=fixture()
    try:
        assert db.save_player('XINXA_A',2,player_id=a) == a
        assert len(db.players())==2
        assert next(p for p in db.players() if p['id']==a)['stars']==2
        try:
            db.save_match({'id':'match_00'},[{'player_id':a}])
        except ValueError:
            pass
        else:assert False,'Deveria bloquear duplicação'
    finally:folder.cleanup()