-- EDB LEAGUE: linha do tempo dos rounds de cada mapa, gravada na importação da demo (parser v4).
-- Uma linha por partida; "rounds" é uma lista JSON com o vencedor (a ou b), o lado, o motivo, se a bomba foi plantada e o placar acumulado.
-- Tabela aditiva: nada nos rankings depende dela. Sem ela, a importação segue normal e a página da partida não mostra a linha do tempo.
create table if not exists public.match_rounds (
  match_id text primary key,
  rounds jsonb not null,
  created_at timestamptz not null default now()
);
alter table public.match_rounds enable row level security;
