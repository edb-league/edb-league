"""Regras da XINXAS LEAGUE. Sem dependência de interface ou banco."""
from __future__ import annotations
from datetime import date
import pandas as pd

# Metas proporcionais ao nível; ajustar com resultados da primeira temporada.
TARGET_KPR = {1: 0.42, 2: 0.57, 3: 0.72, 4: 0.87, 5: 1.02}
TARGET_ADR = {1: 42.0, 2: 55.0, 3: 69.0, 4: 85.0, 5: 103.0}


def enrich(players: list[dict], matches: list[dict], stats: list[dict]) -> pd.DataFrame:
    """Retorna uma linha por jogador/partida; não fabrica estatísticas faltantes."""
    columns = ['player_id', 'match_id', 'nickname', 'stars', 'map_name', 'played_at',
               'kills', 'deaths', 'assists', 'damage', 'rounds', 'won', 'headshots',
               'plants', 'defuses', 'rating', 'kast', 'open_kills', 'trade_kills']
    if not stats or not players or not matches:
        return pd.DataFrame(columns=columns)
    p = pd.DataFrame(players)[['id','nickname','stars']].rename(columns={'id':'player_id'})
    m = pd.DataFrame(matches)[['id','played_at','map_name','source']].rename(columns={'id':'match_id'})
    s = pd.DataFrame(stats)
    frame = s.merge(p, on='player_id', how='left').merge(m, on='match_id', how='inner')
    frame['played_at'] = pd.to_datetime(frame['played_at'], errors='coerce')
    frame = frame.dropna(subset=['played_at'])
    for name in ['kills','deaths','assists','rounds','headshots','plants','defuses','stars','damage','rating','kast','open_kills','trade_kills']:
        if name not in frame:
            frame[name] = None
        frame[name] = pd.to_numeric(frame[name], errors='coerce')
    frame['stars'] = frame['stars'].fillna(3).astype(int).clip(1,5)
    for name in ['kills','deaths','assists','rounds','headshots','plants','defuses']:
        frame[name] = frame[name].fillna(0)
    frame['kpr'] = frame['kills'] / frame['rounds'].replace(0, float('nan'))
    frame['adr'] = frame['damage'] / frame['rounds'].replace(0, float('nan'))
    frame['won'] = frame['won'].map(lambda w: True if w in (True,1,'1') else (False if w in (False,0,'0') else None))
    return frame.sort_values('played_at')


def cap_weekly(frame: pd.DataFrame, games_per_week: int = 4) -> pd.DataFrame:
    """Até N primeiras partidas por semana/jogador para os rankings."""
    if frame.empty:
        return frame.copy()
    t = frame.copy().sort_values(['player_id','played_at','match_id'])
    t['week'] = t['played_at'].dt.strftime('%G-W%V')
    t['eligible_game'] = t.groupby(['player_id','week']).cumcount() < games_per_week
    return t


def leaderboard(frame: pd.DataFrame, min_games: int = 2) -> pd.DataFrame:
    columns = ['Jogador','Estrelas','Partidas','Kills','K/D','KPR','ADR','Vitórias','Elite','Superação %','XP']
    if frame.empty:
        return pd.DataFrame(columns=columns)
    t = cap_weekly(frame)
    eligible = t[t['eligible_game']].copy()
    rows = []
    for pid, g in eligible.groupby('player_id', sort=False):
        first = g.iloc[0]
        kills, deaths = int(g['kills'].sum()), int(g['deaths'].sum())
        rounds = max(float(g['rounds'].sum()), 1)
        kpr = kills/rounds
        n_dmg = g['damage'].notna().sum()
        adr = float(g['damage'].sum())/rounds if n_dmg == len(g) else float('nan')
        skill = int(first['stars'])
        elite = 100 * ((0.6*kpr/0.75) + (0.4*adr/75)) if pd.notna(adr) else 100*kpr/0.75
        # Superação estimada pelas estrelas, não "melhoria histórica".
        relative = 100 * (kpr/TARGET_KPR[skill] - 1)
        g = g.sort_values('played_at')
        win_count = int((g['won'] == True).sum())
        xp = xp_for_games(g, skill)
        rows.append({'player_id':pid, 'Jogador':first['nickname'], 'Estrelas':skill,
                     'Partidas':len(g),'Kills':kills,'K/D':round(kills/max(deaths,1),2),
                     'KPR':round(kpr,3),'ADR':round(adr,1) if pd.notna(adr) else None,
                     'Vitórias':win_count,'Elite':round(elite,1),'Superação %':round(relative,1),
                     'XP':xp,'Elegível':len(g)>=min_games})
    return pd.DataFrame(rows).sort_values(['Elite','KPR'],ascending=False).reset_index(drop=True)


def xp_for_games(g: pd.DataFrame, stars: int) -> int:
    """Máximo: 40 XP por presença + 20 por vitória + 100 por missão/semana.

    Partidas além do teto semanal já foram retiradas de g pelo chamador.
    """
    xp = 40 * len(g) + 20 * int((g['won']==True).sum())
    t = g.copy()
    t['week'] = t['played_at'].dt.strftime('%G-W%V')
    for _, week_games in t.groupby('week'):
        qualified = ((week_games['kpr'] >= TARGET_KPR[stars]) & (week_games['rounds'] >= 8)).any()
        if qualified:
            xp += 100
    return int(xp)


def historical_progress(frame: pd.DataFrame) -> pd.DataFrame:
    """Comparação das últimas 2 partidas às 2 anteriores; exige quatro jogos."""
    rows=[]
    if frame.empty:
        return pd.DataFrame(columns=['Jogador','Evolução %','Jogos'])
    for pid, g in frame.sort_values('played_at').groupby('player_id'):
        if len(g)<4:
            continue
        tail=g.tail(4)
        prev=tail.iloc[:2]; recent=tail.iloc[2:]
        before=prev['kills'].sum()/max(prev['rounds'].sum(),1)
        after=recent['kills'].sum()/max(recent['rounds'].sum(),1)
        if before:
            rows.append({'Jogador':g.iloc[-1]['nickname'], 'Evolução %':round(100*(after/before-1),1), 'Jogos':len(g)})
    return pd.DataFrame(rows).sort_values('Evolução %',ascending=False) if rows else pd.DataFrame(columns=['Jogador','Evolução %','Jogos'])


def weekly_awards(frame: pd.DataFrame) -> dict:
    if frame.empty:
        return {}
    t=cap_weekly(frame)
    t=t[t['eligible_game']]
    if t.empty:
        return {}
    board=leaderboard(t,min_games=2)
    awards={}
    qualified=board[board['Elegível']]
    if not qualified.empty:
        awards['MVP de performance']=qualified.sort_values('Elite',ascending=False).iloc[0]['Jogador']
        awards['Superação']=qualified.sort_values('Superação %',ascending=False).iloc[0]['Jogador']
    best=board.sort_values('Kills',ascending=False)
    if not best.empty:
        awards['Máquina de guerra']=best.iloc[0]['Jogador']
    assists=t.groupby('nickname',dropna=True)['assists'].sum().sort_values(ascending=False)
    if not assists.empty:
        awards['Parceiro de guerra']=assists.index[0]
    return awards