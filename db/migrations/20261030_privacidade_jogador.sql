-- EDB LEAGUE: escolhas de privacidade de cada jogador sobre a conta Steam (foto, nome na Steam, horas de CS).
-- Padrão (sem linha): tudo aparece, como antes. Só a API (chave de serviço) lê e grava; RLS ligada sem políticas.
-- Sem esta tabela o site funciona normalmente e as opções aparecem como indisponíveis.
create table if not exists public.player_privacy (
  player_id text primary key,
  hide_avatar boolean not null default false,
  hide_persona boolean not null default false,
  hide_hours boolean not null default false,
  updated_at timestamptz not null default now()
);
alter table public.player_privacy enable row level security;
