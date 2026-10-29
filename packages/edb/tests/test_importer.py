import io, gzip, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from edb.demo_importer import prepare_upload, parse_demo

class Upload(io.BytesIO):
    def __init__(self, content, name):
        super().__init__(content);self.name=name

class FakeParser:
    def __init__(self, p):pass
    def parse_header(self):return {'map_name':'de_inferno'}
    def parse_player_info(self):
        return pd.DataFrame({'steamid':['76561198000000001','76561198000000002'],'name':['AA','BB']})
    def parse_event(self,name,other=None):
        tick=10000
        data={
            'player_death':pd.DataFrame([{'attacker_steamid':'76561198000000001','user_steamid':'76561198000000002',
                'attacker_name':'AA','user_name':'BB','headshot':True,'tick':tick,'total_rounds_played':0}]),
            'player_hurt':pd.DataFrame([{'attacker_steamid':'76561198000000001','user_steamid':'76561198000000002',
                'attacker_name':'AA','user_name':'BB','dmg_health':80,'tick':tick,'total_rounds_played':0}]),
            'player_spawn':pd.DataFrame([
                {'user_steamid':'76561198000000001','user_name':'AA','total_rounds_played':0,'tick':9000},
                {'user_steamid':'76561198000000002','user_name':'BB','total_rounds_played':0,'tick':9000}]),
            'round_end':pd.DataFrame([{'winner':'CT','tick':11000,'total_rounds_played':0}]),
            'bomb_planted':pd.DataFrame([{'user_steamid':'76561198000000001','user_name':'AA','tick':10002,'total_rounds_played':0}])
        }
        return data.get(name,pd.DataFrame())

def test_importer_extraction(monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setitem(sys.modules,'demoparser2',SimpleNamespace(DemoParser=FakeParser))
    result=parse_demo('dummy.dem','abc')
    assert result.map_name=='Inferno'
    assert result.rounds_total==1
    a=next(p for p in result.players if p['nickname']=='AA')
    assert a['kills']==1 and a['headshots']==1 and a['damage']==80 and a['plants']==1
    assert a['rounds']==1

def test_prepare_gzip():
    content=b'PBDEMS2'+b'0'*3000
    upload=Upload(gzip.compress(content),'sample.dem.gz')
    folder,path,fingerprint=prepare_upload(upload)
    try:
        assert Path(path).read_bytes()==content
        assert len(fingerprint)==64
    finally:folder.cleanup()

class WarmupParser(FakeParser):
    """Inclui um aquecimento, dois frags oficiais, um TK e um evento após round_end."""
    def parse_event(self, name, other=None):
        warm={'tick':100,'total_rounds_played':0,'is_warmup_period':True}
        active={'tick':10000,'total_rounds_played':0,'is_warmup_period':False}
        def death(tick, warmup=False, team_kill=False):
            return dict(attacker_steamid='76561198000000001',user_steamid='76561198000000002',
                        attacker_name='AA',user_name='BB',attacker_team_name='CT',
                        user_team_name='CT' if team_kill else 'TERRORIST',
                        headshot=True, tick=tick,total_rounds_played=0,is_warmup_period=warmup)
        events={
            'player_death': [death(100,True),death(10100),death(10200,False,True),death(12000)],
            'player_hurt':[dict(attacker_steamid='76561198000000001',user_steamid='76561198000000002',
                                attacker_team_name='CT',user_team_name='TERRORIST',
                                attacker_name='AA',user_name='BB',dmg_health=50,**warm),
                           dict(attacker_steamid='76561198000000001',user_steamid='76561198000000002',
                                attacker_team_name='CT',user_team_name='TERRORIST',
                                attacker_name='AA',user_name='BB',dmg_health=70,**active)],
            'round_start':[dict(tick=9000,total_rounds_played=0,is_warmup_period=False)],
            'round_end':[dict(tick=900,total_rounds_played=0,is_warmup_period=True),
                         dict(tick=11000,total_rounds_played=0,is_warmup_period=False)],
            'player_spawn':[dict(user_steamid='76561198000000001',user_name='AA',**warm),
                            dict(user_steamid='76561198000000001',user_name='AA',**active),
                            dict(user_steamid='76561198000000002',user_name='BB',**active)],
            'bomb_planted':[dict(user_steamid='76561198000000001',user_name='AA',**warm),
                            dict(user_steamid='76561198000000001',user_name='AA',**active)],
        }
        return pd.DataFrame(events.get(name,[]))


def test_warmup_teamkill_and_post_round_are_ignored(monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setitem(sys.modules,'demoparser2',SimpleNamespace(DemoParser=WarmupParser))
    result=parse_demo('dummy.dem','warmtest')
    aa=next(p for p in result.players if p['nickname']=='AA')
    assert result.rounds_total==1
    assert aa['kills']==1  # Não 4: exclui aquecimento, TK e depois de round_end
    assert aa['headshots']==1
    assert aa['damage']==70
    assert aa['plants']==1
    assert aa['rounds']==1


def test_warmup_flag_filter():
    from edb.demo_importer import _trim_warmup
    f=pd.DataFrame({'tick':[1,2,3], 'is_warmup_period':[True,False,'true']})
    filtered=_trim_warmup(f)
    assert filtered['tick'].tolist()==[2]

class OverkillParser(FakeParser):
    """AWP em quem tinha 20 de vida: dmg_health=100, mas só 20 de dano efetivo."""
    def parse_event(self, name, other=None):
        if name == 'player_hurt':
            ids = dict(attacker_steamid='76561198000000001', user_steamid='76561198000000002',
                       attacker_name='AA', user_name='BB', total_rounds_played=0)
            return pd.DataFrame([
                dict(ids, dmg_health=80, health=20, tick=10000),
                dict(ids, dmg_health=100, health=0, tick=10010),
            ])
        return super().parse_event(name, other)


def test_damage_is_capped_at_remaining_health(monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setitem(sys.modules, 'demoparser2', SimpleNamespace(DemoParser=OverkillParser))
    result = parse_demo('dummy.dem', 'abc')
    a = next(p for p in result.players if p['nickname'] == 'AA')
    assert a['damage'] == 100


class FirstRoundSpawnParser(FakeParser):
    """Três rounds oficiais; o spawn do primeiro fica fora do filtro (antes do begin_new_match)."""
    def parse_event(self, name, other=None):
        ids = ('76561198000000001', '76561198000000002')
        if name == 'player_spawn':
            return pd.DataFrame([dict(user_steamid=s, user_name=n, total_rounds_played=r, tick=9000 + r)
                                 for s, n in zip(ids, ('AA', 'BB')) for r in (1, 2)])
        if name == 'round_end':
            return pd.DataFrame([dict(winner='CT', tick=10100 + 1000 * r, total_rounds_played=r) for r in (0, 1, 2)])
        return super().parse_event(name, other)


def test_player_rounds_include_first_round_spawn_outside_filter(monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setitem(sys.modules, 'demoparser2', SimpleNamespace(DemoParser=FirstRoundSpawnParser))
    result = parse_demo('dummy.dem', 'abc')
    assert result.rounds_total == 3
    assert all(p['rounds'] == 3 for p in result.players)


def test_prepare_accepts_plain_gz_name():
    content=b'PBDEMS2'+b'0'*3000
    folder,path,_=prepare_upload(Upload(gzip.compress(content),'md1_inferno_20_10.gz'))
    try:
        assert Path(path).read_bytes()==content
    finally:folder.cleanup()


def _analysis(t_score=13,ct_score=9):
    from edb.demo_stats import COUNT_FIELDS
    def player(i,team):
        row={f:0 for f in COUNT_FIELDS}
        row.update(steamid=str(76561198000000000+i),nick=f'P{i}',team=team,rounds=t_score+ct_score,
                   kills=15,deaths=12,assists=3,damage=1700,headshots=6,plants=1,defuses=0,
                   kast=72,open_kills=2,trade_kills=1,kills_t=8,kills_ct=7,deaths_t=6,deaths_ct=6,
                   damage_t=900,damage_ct=800,rounds_t=11,rounds_ct=11)
        return row
    return {'map':'inferno','rounds':t_score+ct_score,'score':{'team_t_first':t_score,'team_ct_first':ct_score},
            'players':[player(i,2 if i<5 else 3) for i in range(10)]}


def test_parse_demo_stats_maps_analysis_and_winner(monkeypatch):
    from edb import demo_importer, demo_stats
    monkeypatch.setattr(demo_stats,'analyze',lambda path:_analysis(13,9))
    result=demo_importer.parse_demo_stats('dummy.dem','abc')
    assert result.map_name=='Inferno' and result.rounds_total==22 and len(result.players)==10
    first=result.players[0]
    assert first['nickname']=='P0' and first['kast']==72 and first['rounds']==22 and first['damage']==1700
    assert first['rating'] is not None
    # Quem começou de T (team 2) venceu por 13x9.
    assert [p['won'] for p in result.players]==[True]*5+[False]*5


def test_parse_demo_stats_tie_leaves_winner_open(monkeypatch):
    from edb import demo_importer, demo_stats
    monkeypatch.setattr(demo_stats,'analyze',lambda path:_analysis(11,11))
    result=demo_importer.parse_demo_stats('dummy.dem','abc')
    assert all(p['won'] is None for p in result.players)
    assert any('empatado' in w for w in result.warnings)
