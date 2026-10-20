"""Persistência SQLite local ou Supabase PostgREST na nuvem.

Chaves Supabase são usadas APENAS pelo servidor, nunca no navegador.
"""
from __future__ import annotations
import sqlite3
from pathlib import Path
from uuid import uuid4
import requests

ROOT=Path(__file__).resolve().parent
DB_FILE=ROOT/'xinxas.db'
FIELDS_STATS=['match_id','player_id','kills','deaths','assists','damage','rounds',
              'won','headshots','plants','defuses','rating','kast','open_kills','trade_kills','observed_nickname']


class Store:
    def __init__(self, url='', key='', db_file=None):
        self.url=url.rstrip('/')
        self.key=key
        self.cloud=bool(self.url and self.key)
        if bool(self.url) != bool(self.key):
            raise ValueError('Configure SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY juntos.')
        self.db_file=Path(db_file) if db_file else DB_FILE
        if not self.cloud:
            self._init_db()

    def _connect(self):
        con=sqlite3.connect(str(self.db_file), timeout=30)
        con.row_factory=sqlite3.Row
        con.execute('PRAGMA foreign_keys = ON')
        return con

    def _init_db(self):
        self.db_file.parent.mkdir(parents=True,exist_ok=True)
        with self._connect() as con:
            con.executescript('''
            CREATE TABLE IF NOT EXISTS players (
                id TEXT PRIMARY KEY, nickname TEXT NOT NULL,
                steamid TEXT UNIQUE, stars INTEGER NOT NULL DEFAULT 3,
                skill_level INTEGER NOT NULL DEFAULT 5 CHECK(skill_level BETWEEN 1 AND 10),
                is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS matches (
                id TEXT PRIMARY KEY, played_at TEXT NOT NULL, map_name TEXT,
                source TEXT NOT NULL, rounds_total INTEGER, notes TEXT
            );
            CREATE TABLE IF NOT EXISTS player_stats (
                match_id TEXT NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
                player_id TEXT NOT NULL REFERENCES players(id) ON DELETE CASCADE,
                kills INTEGER NOT NULL DEFAULT 0,
                deaths INTEGER NOT NULL DEFAULT 0,
                assists INTEGER NOT NULL DEFAULT 0,
                damage INTEGER, rounds INTEGER NOT NULL DEFAULT 0,
                won INTEGER, headshots INTEGER NOT NULL DEFAULT 0,
                plants INTEGER NOT NULL DEFAULT 0,
                defuses INTEGER NOT NULL DEFAULT 0,
                rating REAL, kast REAL, open_kills INTEGER, trade_kills INTEGER,
                observed_nickname TEXT,
                PRIMARY KEY (match_id, player_id)
            );
            ''')
            player_cols = [r[1] for r in con.execute('PRAGMA table_info(players)')]
            if 'skill_level' not in player_cols:
                con.execute('ALTER TABLE players ADD COLUMN skill_level INTEGER NOT NULL DEFAULT 5')
            if 'is_active' not in player_cols:
                con.execute('ALTER TABLE players ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1')
            cols = [r[1] for r in con.execute('PRAGMA table_info(player_stats)')]
            if 'observed_nickname' not in cols:
                con.execute('ALTER TABLE player_stats ADD COLUMN observed_nickname TEXT')

    def _api(self, method, table, *, params=None, payload=None):
        headers={'apikey':self.key,'Authorization':'Bearer '+self.key,
                 'Content-Type':'application/json','Prefer':'return=representation,resolution=merge-duplicates'}
        resp=requests.request(method,self.url+'/rest/v1/'+table,headers=headers,
                              params=params,json=payload,timeout=45)
        if not resp.ok:
            raise RuntimeError(f'Falha no banco ({resp.status_code}): {resp.text[:400]}')
        return resp.json() if resp.content else []

    def _list(self,table):
        if self.cloud:
            rows=[]; offset=0
            while True:
                batch=self._api('GET',table,params={'select':'*','limit':'1000','offset':str(offset)})
                rows.extend(batch)
                if len(batch)<1000: return rows
                offset+=1000
        with self._connect() as con:
            return [dict(row) for row in con.execute('SELECT * FROM '+table)]

    def players(self): return self._list('players')
    def matches(self): return self._list('matches')
    def stats(self): return self._list('player_stats')
    def scope_stats(self):
        """Dados extras do SCOPE.GG: mira, granadas e ADR oficial (somente online)."""
        return self._list('player_scope_stats') if self.cloud else []

    def _upsert(self,table,row,conflict=None):
        if self.cloud:
            params={'on_conflict':conflict} if conflict else None
            return self._api('POST',table,params=params,payload=row)
        columns=list(row)
        sql=f"INSERT INTO {table} ({','.join(columns)}) VALUES ({','.join('?'*len(columns))}) ON CONFLICT DO UPDATE SET " + ','.join(f'{c}=excluded.{c}' for c in columns if c not in ('id','match_id','player_id'))
        with self._connect() as con: con.execute(sql,list(row.values()))

    def save_player(self, nickname, stars=3, steamid=None, player_id=None, skill_level=None):
        """Identidade estável: SteamID primeiro, depois nick oficial ou alias.

        O nickname oficial só muda em edição administrativa explícita (player_id).
        Uma importação usando outro nick não renomeia a conta nem redefine estrelas.
        """
        nickname = nickname.strip()
        if not nickname: raise ValueError('Nickname obrigatório')
        stars = int(stars)
        if not 1 <= stars <= 5: raise ValueError('Estrelas fora do intervalo 1–5')
        if skill_level is not None:
            skill_level=int(skill_level)
            if not 1 <= skill_level <= 10:
                raise ValueError('Nível fora do intervalo 1–10')
        current = self.players()
        explicit_edit = player_id is not None
        match = next((p for p in current if p['id'] == player_id), None) if explicit_edit else None

        if match is None and steamid:
            match = next((p for p in current if p.get('steamid') == steamid), None)
        if match is None:
            match = next((p for p in current if p['nickname'].casefold() == nickname.casefold()), None)
        if match is None and self.cloud:
            aliases = self._list('player_aliases')
            alias = next((a for a in aliases if a['alias'].casefold() == nickname.casefold()), None)
            if alias:
                match = next((p for p in current if p['id'] == alias['player_id']), None)

        if match is not None:
            player_id = match['id']
            steamid = steamid or match.get('steamid')
            if not explicit_edit:
                nickname = match['nickname']
                stars = int(match['stars'])
        if skill_level is None:
            skill_level = int(match.get('skill_level',5)) if match else 5
        pid = player_id or str(uuid4())
        row = {'id': pid, 'nickname': nickname, 'steamid': steamid or None,
               'stars': stars, 'skill_level': skill_level}
        if self.cloud:
            self._upsert('players', row, 'id')
        else:
            with self._connect() as con:
                con.execute('''INSERT INTO players (id,nickname,steamid,stars,skill_level)
                               VALUES (:id,:nickname,:steamid,:stars,:skill_level)
                               ON CONFLICT(id) DO UPDATE SET nickname=excluded.nickname,
                               steamid=COALESCE(excluded.steamid,players.steamid),
                               stars=excluded.stars,skill_level=excluded.skill_level''', row)
        return pid

    def set_player_active(self, player_id, active):
        """Retira ou reativa um jogador sem excluir dados de temporadas e partidas."""
        pid = str(player_id).strip()
        if not pid or not isinstance(active, bool):
            raise ValueError('Jogador e situação válidos são obrigatórios.')
        if self.cloud:
            changed = self._api('PATCH', 'players',
                                params={'id': 'eq.' + pid},
                                payload={'is_active': active})
            if len(changed) != 1:
                raise ValueError('Jogador não encontrado.')
        else:
            with self._connect() as con:
                cursor = con.execute(
                    'UPDATE players SET is_active=? WHERE id=?',
                    (int(active), pid),
                )
                if cursor.rowcount != 1:
                    raise ValueError('Jogador não encontrado.')

    def match_exists(self,mid):
        if self.cloud:
            return bool(self._api('GET','matches',params={'id':'eq.'+mid,'select':'id'}))
        with self._connect() as con:
            return con.execute('SELECT 1 FROM matches WHERE id=?',(mid,)).fetchone() is not None

    def save_match(self,match,lines):
        """Match ID único; impedir duplicidade. Garantia atômica para SQLite."""
        if not lines: raise ValueError('Partida sem jogadores')
        if self.match_exists(match['id']):
            raise ValueError('Essa partida já foi registrada.')
        if self.cloud:
            # Na API REST as duas inserções não são transacionais.
            # Em falha, admin deverá completar/corrigir no Supabase.
            self._upsert('matches',match,'id')
            try:
                self._api('POST','player_stats',params={'on_conflict':'match_id,player_id'},
                          payload=[{k:line.get(k) for k in FIELDS_STATS} for line in lines])
            except Exception as e:
                self._api('DELETE','matches',params={'id':'eq.'+match['id']})
                raise RuntimeError(f'Não foi possível salvar os jogadores: {e}') from e
        else:
            cols=['id','played_at','map_name','source','rounds_total','notes']
            match={k:match.get(k) for k in cols}
            with self._connect() as con:
                con.execute('INSERT INTO matches ('+','.join(cols)+') VALUES ('+','.join(':'+c for c in cols)+')',match)
                for line in lines:
                    line={k:line.get(k) for k in FIELDS_STATS}
                    con.execute('INSERT INTO player_stats ('+','.join(FIELDS_STATS)+') VALUES ('+','.join(':'+c for c in FIELDS_STATS)+')',line)