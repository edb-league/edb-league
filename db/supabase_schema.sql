-- Executar UMA vez no SQL Editor do Supabase.
-- As tabelas ficam protegidas por RLS. Somente a chave de SERVIÇO usada no
-- servidor Streamlit acessa esses dados; nunca colocar essa chave no front-end.
create table if not exists public.players (
 id text primary key, nickname text not null, steamid text unique,
 stars integer not null default 3 check (stars between 1 and 5),
 created_at timestamptz not null default now()
);
create table if not exists public.matches (
 id text primary key, played_at date not null, map_name text,
 source text not null, rounds_total integer, notes text
);
create table if not exists public.player_stats (
 match_id text not null references public.matches(id) on delete cascade,
 player_id text not null references public.players(id) on delete cascade,
 kills integer not null default 0, deaths integer not null default 0,
 assists integer not null default 0, damage integer, rounds integer not null default 0,
 won boolean, headshots integer not null default 0,
 plants integer not null default 0, defuses integer not null default 0,
 rating double precision, kast double precision,
 open_kills integer, trade_kills integer,
 primary key (match_id,player_id)
);
alter table public.players enable row level security;
alter table public.matches enable row level security;
alter table public.player_stats enable row level security;
-- Não criar policies para anon/authenticated: sem acesso direto do navegador.

-- Votação de MVP da partida (ver db/migrations/20261030_votacao_mvp.sql).
create table if not exists public.match_mvp_votes (
  match_id text not null, voter_id text not null, candidate_id text not null,
  created_at timestamptz not null default now(),
  primary key (match_id, voter_id), check (voter_id <> candidate_id)
);
alter table public.match_mvp_votes enable row level security;
