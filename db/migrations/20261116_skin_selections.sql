-- Escolhas de skin feitas no site, lidas pela ponte que roda no servidor de CS2 e copia para o WeaponPaints.
-- Tabela nova: nenhuma tabela existente é alterada. Só a API (chave de serviço) acessa; sem política pública.
-- `deleted` marca remoções para a ponte também apagar a skin no jogo.
create table if not exists public.skin_selections (
  steamid text not null,
  weapon_id integer not null,
  paint_id integer not null default 0,
  wear real not null default 0.01 check (wear >= 0 and wear <= 1),
  seed integer not null default 0 check (seed >= 0 and seed <= 1000),
  deleted boolean not null default false,
  updated_at timestamptz not null default now(),
  primary key (steamid, weapon_id)
);
create index if not exists skin_selections_updated_at_idx on public.skin_selections (updated_at);
alter table public.skin_selections enable row level security;
