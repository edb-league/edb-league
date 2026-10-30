-- EDB LEAGUE: votação de MVP da partida (um voto por jogador e mapa; pode ser trocado enquanto a votação está aberta).
-- Tabela aditiva: não altera rankings, XP nem títulos. Só a API (chave de serviço) lê e grava; RLS fica ligada sem políticas.
-- Sem esta tabela o site continua normal e a votação aparece como indisponível.
create table if not exists public.match_mvp_votes (
  match_id text not null,
  voter_id text not null,
  candidate_id text not null,
  created_at timestamptz not null default now(),
  primary key (match_id, voter_id),
  check (voter_id <> candidate_id)
);
create index if not exists match_mvp_votes_match_idx on public.match_mvp_votes (match_id);
alter table public.match_mvp_votes enable row level security;
