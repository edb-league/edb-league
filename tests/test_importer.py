import io, gzip, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from demo_importer import prepare_upload, parse_demo

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