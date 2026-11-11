-- Draft de campeonato: um documento JSON por draft (a API usa a chave de serviço; sem política de acesso público).
create table if not exists public.league_drafts (
  id text primary key,
  data jsonb not null,
  updated_at timestamptz not null default now()
);
alter table public.league_drafts enable row level security;
