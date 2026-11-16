-- Lobby de partidas do servidor: um documento JSON por lobby (a API usa a chave de serviço; sem política de acesso público).
-- Tabela nova: nenhuma tabela existente é alterada.
create table if not exists public.league_lobbies (
  id text primary key,
  data jsonb not null,
  updated_at timestamptz not null default now()
);
alter table public.league_lobbies enable row level security;
