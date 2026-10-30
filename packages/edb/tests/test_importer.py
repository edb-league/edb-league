import io, gzip, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pytest
from edb.demo_importer import prepare_upload, _validate_combat_stats

class Upload(io.BytesIO):
    def __init__(self, content, name):
        super().__init__(content);self.name=name

def test_prepare_gzip():
    content=b'PBDEMS2'+b'0'*3000
    upload=Upload(gzip.compress(content),'sample.dem.gz')
    folder,path,fingerprint=prepare_upload(upload)
    try:
        assert Path(path).read_bytes()==content
        assert len(fingerprint)==64
    finally:folder.cleanup()


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


def test_prepare_accepts_plain_dem_upload():
    content=b'PBDEMS2'+b'0'*3000
    folder,path,fingerprint=prepare_upload(Upload(content,'md1_inferno_20_10.dem'))
    try:
        assert Path(path).read_bytes()==content and len(fingerprint)==64
    finally:folder.cleanup()


def test_no_valid_kills_or_deaths_is_a_hard_failure():
    with pytest.raises(ValueError,match="não foi possível extrair"):
        _validate_combat_stats([{"kills":0,"deaths":0,"rounds":20}],20)
    with pytest.raises(ValueError,match="não foi possível extrair"):
        _validate_combat_stats([{"kills":15,"deaths":0,"rounds":20}],20)


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
