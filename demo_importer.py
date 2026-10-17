"""Importador de .dem ou .dem.gz do Counter-Strike 2.

Usa demoparser2 (a instalar no computador/servidor de execução).
Estatísticas de rating, KAST e trades NÃO são inferidas; não equivalem ao SCOPE.
Toda importação deve ser revisada pelo administrador antes de gravar.
"""
from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict
from pathlib import Path
import gzip
import hashlib
import shutil
import tempfile
import pandas as pd

MAX_UNCOMPRESSED = 1024 * 1024 * 1024  # 1 GB

@dataclass
class DemoOutput:
    fingerprint: str
    map_name: str
    rounds_total: int
    players: list[dict]
    warnings: list[str]


def prepare_upload(uploaded):
    """Descompacta em blocos, verifica limite, e devolve (TemporaryDirectory, path, sha256)."""
    folder = tempfile.TemporaryDirectory(prefix='xinxas_')
    is_gz = str(uploaded.name).lower().endswith('.gz')
    if not str(uploaded.name).lower().endswith(('.dem','.dem.gz')):
        folder.cleanup()
        raise ValueError('Formato não suportado: utilize .dem ou .dem.gz')
    out = Path(folder.name)/'partida.dem'
    uploaded.seek(0)
    sha = hashlib.sha256(); size=0
    try:
        raw = gzip.GzipFile(fileobj=uploaded) if is_gz else uploaded
        with raw, open(out,'wb') as dest:
            while True:
                b=raw.read(1024*1024)
                if not b: break
                size+=len(b)
                if size>MAX_UNCOMPRESSED:
                    raise ValueError('Demo descompactada excede 1 GB')
                sha.update(b); dest.write(b)
        if size<1024:
            raise ValueError('Arquivo muito pequeno para conter uma demo válida')
        return folder, str(out), sha.hexdigest()
    except Exception:
        folder.cleanup(); raise


def _s(value):
    if value is None or pd.isna(value): return ''
    if isinstance(value,(float,int)):
        return str(int(value))
    return str(value).strip()


def _number(value):
    try:
        v=float(value)
        return max(v,0) if pd.notna(v) else 0.0
    except (TypeError,ValueError):
        return 0.0


def _event(parser,name,other=None):
    try:
        df=parser.parse_event(name,other=other) if other else parser.parse_event(name)
        return df if isinstance(df,pd.DataFrame) else pd.DataFrame(df)
    except Exception:
        return pd.DataFrame()


def _header_map(header):
    if isinstance(header,dict):
        for key in ('map_name','map','mapName'):
            if header.get(key):
                return str(header[key]).replace('de_','').title()
    return 'Não identificado'


def parse_demo(dem_path: str, fingerprint: str) -> DemoOutput:
    from demoparser2 import DemoParser
    parser=DemoParser(dem_path)
    warns=[]
    try:
        header=parser.parse_header()
    except Exception:
        header={}
    deaths=_event(parser,'player_death',other=['total_rounds_played'])
    if deaths.empty or not {'attacker_steamid','user_steamid'}.issubset(deaths.columns):
        raise ValueError('A demo não trouxe eventos de mortes reconhecíveis pelo parser.')
    hurts=_event(parser,'player_hurt',other=['total_rounds_played'])
    spawns=_event(parser,'player_spawn',other=['total_rounds_played'])
    round_ends=_event(parser,'round_end',other=['total_rounds_played'])
    bombs_planted=_event(parser,'bomb_planted',other=['total_rounds_played'])
    bombs_defused=_event(parser,'bomb_defused',other=['total_rounds_played'])
    warns.append('Confirme o placar e o número de rounds antes de salvar; warmup/substituições podem afetar a contagem.')
    # Quando há evento explícito do fim do aquecimento, excluímos eventos anteriores.
    warm=_event(parser,'round_announce_match_start')
    if warm.empty:
        warm=_event(parser,'warmup_end')
    if not warm.empty and 'tick' in warm.columns:
        ticks=pd.to_numeric(warm['tick'],errors='coerce').dropna()
        min_tick=int(ticks.min()) if not ticks.empty else None
        if min_tick is not None:
            deaths=deaths[deaths['tick']>=min_tick]
            if 'tick' in hurts: hurts=hurts[hurts['tick']>=min_tick]
            if 'tick' in spawns: spawns=spawns[spawns['tick']>=min_tick]
            if 'tick' in round_ends: round_ends=round_ends[round_ends['tick']>=min_tick]
            if 'tick' in bombs_planted: bombs_planted=bombs_planted[bombs_planted['tick']>=min_tick]
            if 'tick' in bombs_defused: bombs_defused=bombs_defused[bombs_defused['tick']>=min_tick]
    players=defaultdict(lambda: {'nickname':'', 'steamid':'','kills':0,'deaths':0,'assists':0,
                                 'damage':0,'rounds':0,'headshots':0,'plants':0,'defuses':0,
                                 'rating':None,'kast':None,'open_kills':None,'trade_kills':None})
    def add(steam,name):
        sid=_s(steam)
        if not sid or sid in ('0','-1','nan','None'): return None
        p=players[sid]
        p['steamid']=sid
        if name and str(name) not in ('nan','None'):
            p['nickname']=str(name)
        return p
    try:
        info=parser.parse_player_info()
        if isinstance(info,pd.DataFrame):
            for _,r in info.iterrows():
                add(r.get('steamid',r.get('steam_id')),r.get('name',r.get('player_name')))
    except Exception:
        pass
    for _,r in deaths.iterrows():
        victim=add(r.get('user_steamid'),r.get('user_name'))
        attacker=add(r.get('attacker_steamid'),r.get('attacker_name'))
        aid=_s(r.get('attacker_steamid')); vid=_s(r.get('user_steamid'))
        if victim is not None:
            victim['deaths']+=1
        if attacker is not None and aid!=vid:
            attacker['kills']+=1
            if str(r.get('headshot',False)).lower() in ('true','1'):
                attacker['headshots']+=1
        assister=add(r.get('assister_steamid'),r.get('assister_name'))
        if assister is not None and _s(r.get('assister_steamid')) not in (vid,aid):
            assister['assists']+=1
    if not hurts.empty and 'dmg_health' in hurts.columns:
        for _,r in hurts.iterrows():
            a=add(r.get('attacker_steamid'),r.get('attacker_name'))
            if a is None or _s(r.get('user_steamid')) == _s(r.get('attacker_steamid')):continue
            # Não contabilizar dano do próprio jogador; confirmar friendly-fire em review.
            a['damage']+=int(_number(r.get('dmg_health')))
    else:
        warns.append('Dano não encontrado: ADR ficará indisponível.')
    for events,key in [(bombs_planted,'plants'),(bombs_defused,'defuses')]:
        for _,r in events.iterrows():
            p=add(r.get('user_steamid'),r.get('user_name'))
            if p is not None: p[key]+=1
    if not spawns.empty and 'total_rounds_played' in spawns.columns:
        seen=defaultdict(set)
        for _,r in spawns.iterrows():
            sid=_s(r.get('user_steamid')); rnd=_s(r.get('total_rounds_played'))
            if add(sid,r.get('user_name')) is not None and rnd:
                seen[sid].add(rnd)
        for sid,rounds in seen.items():
            players[sid]['rounds']=len(rounds)
    else:
        warns.append('Sem player_spawn por round; informe rounds jogados manualmente.')
    if not round_ends.empty:
        if 'total_rounds_played' in round_ends.columns:
            total=int(round_ends['total_rounds_played'].nunique())
        else:
            total=len(round_ends)
    else:
        total=max((p['rounds'] for p in players.values()),default=0)
        warns.append('Sem round_end; placar total não confirmado.')
    result=[]
    for _,p in players.items():
        if p['kills']+p['deaths']+p['assists']+p['rounds']+p['plants']+p['defuses']==0:
            continue
        if not p['nickname']:
            p['nickname']='Steam '+p['steamid'][-6:]
        p['damage']=int(p['damage']) if not hurts.empty and 'dmg_health' in hurts else None
        result.append(dict(p))
    if not 8<=len(result)<=12:
        warns.append(f'{len(result)} participantes reconhecidos; reveja trocas de jogadores ou eventos de aquecimento.')
    return DemoOutput(fingerprint,_header_map(header),total,result,warns)