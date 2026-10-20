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
    """Prioriza o marcador do próprio evento, evitando reinícios tardios de round.

    Em demos xplay/CS2 o evento match_start pode ocorrer mais de uma vez.
    Aplicar também um tick posterior a eventos já marcados como oficiais
    apagava eliminações legítimas, enquanto player_spawn ainda dava rounds.
    """
    if df.empty:
        return df
    if 'is_warmup_period' in df.columns:
        flag = df['is_warmup_period'].astype(str).str.lower().str.strip()
        recognized = flag.isin(('true', 'false', '1', '0'))
        if recognized.any():
            return df[~flag.isin(('true', '1'))].copy()
    if match_tick is not None and 'tick' in df.columns:
        df = df[pd.to_numeric(df['tick'], errors='coerce') >= match_tick]
    return df.copy()


def _trim_outside_rounds(df, starts, ends):
    """Filtra rounds sem pressupor que round_start/death/end usam o mesmo índice.

    O total_rounds_played pode avançar exatamente no round_end: um filtro por
    número de round descartaria *todas* as kills apesar do match ser válido.
    Reconstruímos também intervalos pelos ticks reais dos eventos.
    """
    if df.empty or not ends or 'tick' not in df.columns:
        return df
    from bisect import bisect_left
    ticks = pd.to_numeric(df['tick'], errors='coerce')

    # Intervalos oficiais: próximo round_end posterior a cada round_start.
    start_ticks = sorted(set(int(x) for x in starts.values()))
    end_ticks = sorted(set(int(x) for x in ends.values()))
    intervals = []
    for beginning in start_ticks:
        pos = bisect_left(end_ticks, beginning)
        if pos < len(end_ticks):
            intervals.append((beginning, end_ticks[pos]))
    by_tick = pd.Series(False, index=df.index)
    for beginning, ending in intervals:
        by_tick |= ticks.ge(beginning) & ticks.le(ending)

    # Forma antiga, usada apenas se o índice dos três tipos de evento coincidir.
    by_round = pd.Series(False, index=df.index)
    if 'total_rounds_played' in df.columns:
        round_no = pd.to_numeric(df['total_rounds_played'], errors='coerce')
        end_for_round = round_no.map(ends)
        by_round = end_for_round.notna() & ticks.le(end_for_round)
        if starts:
            begin_for_round = round_no.map(starts)
            by_round &= begin_for_round.isna() | ticks.ge(begin_for_round)

    # Não alargar para aquecimento nem escolher por mera coincidência de round.
    # Se a indexação por round estiver deslocada, os ticks preservam as kills.
    keep = by_tick if int(by_tick.sum()) >= int(by_round.sum()) else by_round
    return df[keep].copy()


def _validate_combat_stats(players, rounds_total):
    """Recusa um placar impossível em vez de fabricar dez jogadores 0/0/0."""
    if int(rounds_total) < 1:
        raise ValueError('Nenhum round oficial identificado na demo.')
    kills = sum(int(p.get('kills') or 0) for p in players)
    deaths = sum(int(p.get('deaths') or 0) for p in players)
    if kills <= 0 or deaths <= 0:
        raise ValueError(
            'A demo identificou os jogadores/rounds, mas não foi possível extrair '
            'as eliminações e mortes (K/D = 0). O resultado não foi salvo. '
            'A versão ou a numeração dos eventos pode ser incompatível.'
        )


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
    _validate_combat_stats(result, total)
    if not 8<=len(result)<=12:
        warns.append(f'{len(result)} participantes reconhecidos; reveja trocas de jogadores ou eventos de aquecimento.')
    return DemoOutput(fingerprint,_header_map(header),total,result,warns)