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


def _event(parser, name, other=None, player=None):
    """Consulta eventos, com fallback caso o parser não reconheça is_warmup_period."""
    attempts = [other]
    if other and 'is_warmup_period' in other:
        attempts.append([field for field in other if field != 'is_warmup_period'])
    for fields in attempts:
        # Solicitar team_name para reconhecer TK; alguns parsers antigos não
        # aceitam esse campo, então recuamos ao evento básico sem falhar.
        player_attempts = [player, None] if player else [None]
        for player_fields in player_attempts:
            try:
                options = {}
                if fields: options['other'] = fields
                if player_fields: options['player'] = player_fields
                df = parser.parse_event(name, **options)
                return df if isinstance(df, pd.DataFrame) else pd.DataFrame(df)
            except Exception:
                continue
    return pd.DataFrame()


def _trim_warmup(df, match_tick=None):
    """Exclui eventos marcados como aquecimento e anteriores ao início oficial."""
    if df.empty:
        return df
    if 'is_warmup_period' in df.columns:
        flag = df['is_warmup_period'].astype(str).str.lower().str.strip()
        df = df[~flag.isin(('true', '1'))]
    if match_tick is not None and 'tick' in df.columns:
        df = df[pd.to_numeric(df['tick'], errors='coerce') >= match_tick]
    return df.copy()


def _trim_outside_rounds(df, starts, ends):
    """Descarta ações após o fim de um round ou fora dos rounds finalizados."""
    if df.empty or not ends or 'tick' not in df.columns or 'total_rounds_played' not in df.columns:
        return df
    round_no = pd.to_numeric(df['total_rounds_played'], errors='coerce')
    ticks = pd.to_numeric(df['tick'], errors='coerce')
    end_ticks = round_no.map(ends)
    keep = end_ticks.notna() & ticks.le(end_ticks)
    if starts:
        start_ticks = round_no.map(starts)
        keep &= start_ticks.isna() | ticks.ge(start_ticks)
    return df[keep].copy()


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
    # O demoparser2 oferece a flag is_warmup_period para separar rounds oficiais.
    # Usar somente a primeira aparição do match_start não é suficiente em todas
    # as demos: eventos de aquecimento podem persistir no arquivo.
    fields=['total_rounds_played','is_warmup_period']
    deaths=_event(parser,'player_death',other=fields,player=['team_name'])
    if deaths.empty or not {'attacker_steamid','user_steamid'}.issubset(deaths.columns):
        raise ValueError('A demo não trouxe eventos de mortes reconhecíveis pelo parser.')
    hurts=_event(parser,'player_hurt',other=fields,player=['team_name'])
    spawns=_event(parser,'player_spawn',other=fields)
    round_starts=_event(parser,'round_start',other=fields)
    round_ends=_event(parser,'round_end',other=fields)
    bombs_planted=_event(parser,'bomb_planted',other=fields)
    bombs_defused=_event(parser,'bomb_defused',other=fields)

    warm=_event(parser,'round_announce_match_start')
    if warm.empty:
        warm=_event(parser,'warmup_end')
    ticks=pd.to_numeric(warm['tick'], errors='coerce').dropna() if 'tick' in warm else pd.Series(dtype=float)
    match_tick=int(ticks.min()) if not ticks.empty else None
    if 'is_warmup_period' not in deaths and match_tick is None:
        warns.append('Sem sinal de warmup disponível nesta demo; confira kills e rounds no placar oficial.')
    deaths=_trim_warmup(deaths,match_tick)
    hurts=_trim_warmup(hurts,match_tick)
    spawns=_trim_warmup(spawns,match_tick)
    round_starts=_trim_warmup(round_starts,match_tick)
    round_ends=_trim_warmup(round_ends,match_tick)
    bombs_planted=_trim_warmup(bombs_planted,match_tick)
    bombs_defused=_trim_warmup(bombs_defused,match_tick)
    if round_ends.empty:
        warns.append('Não foram encontrados eventos de fim de round; confira o placar antes de salvar.')

    starts={}
    ends={}
    for df, target in ((round_starts,starts),(round_ends,ends)):
        if df.empty or not {'tick','total_rounds_played'}.issubset(df.columns):
            continue
        for _,r in df.iterrows():
            try:
                rnd=int(r['total_rounds_played']); tick=int(r['tick'])
            except (ValueError,TypeError,OverflowError):
                continue
            # Em caso de restart dentro do round, usamos o início mais recente.
            target[rnd]=max(tick,target.get(rnd,tick))
    if ends:
        deaths=_trim_outside_rounds(deaths,starts,ends)
        hurts=_trim_outside_rounds(hurts,starts,ends)
        bombs_planted=_trim_outside_rounds(bombs_planted,starts,ends)
        bombs_defused=_trim_outside_rounds(bombs_defused,starts,ends)
    warns.append('Revise a pontuação e a data: a demo pode ter substituições ou eventos que exigem conferência.')
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
        # Frags contra aliados não contam como kill no placar competitivo.
        ateam=_s(r.get('attacker_team_name'))
        vteam=_s(r.get('user_team_name'))
        team_kill=bool(ateam and vteam and ateam==vteam)
        if attacker is not None and aid!=vid and not team_kill:
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
            ateam=_s(r.get('attacker_team_name'))
            vteam=_s(r.get('user_team_name'))
            if ateam and vteam and ateam==vteam:continue
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