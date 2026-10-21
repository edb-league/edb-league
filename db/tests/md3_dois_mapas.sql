-- Teste da migração 20261021_md3_dois_mapas.sql em um Postgres descartável (NÃO rode no Supabase).
-- Uso: crie um banco vazio; rode este arquivo; rode a migração; rode db/tests/md3_dois_mapas_cenarios.sql.
create schema auth;
create function auth.role() returns text language sql as $$ select 'service_role'::text $$;
create table league_seasons(number int primary key, starts_on date, ends_on date, homologated_at timestamptz);
create table matches(id text primary key, played_at date, map_name text, rounds_total int, team_a_name text, team_b_name text, team_a_score int, team_b_score int, result_verified bool);
create table player_stats(match_id text references matches(id), player_id text, won bool, primary key(match_id, player_id));
create table bo3_series(id text primary key, season_number int references league_seasons(number), sequence_number int, played_on date, team_a_name text, team_b_name text, status text, winner_side text, match_format text, notes text, unique(season_number, sequence_number));
create table bo3_maps(series_id text references bo3_series(id) on delete cascade, match_id text unique references matches(id), map_number int, winner_side text, primary key(series_id, map_number));
create table bo3_players(series_id text references bo3_series(id) on delete cascade, player_id text, team_side text check (team_side in ('a','b')), primary key(series_id, player_id));
insert into league_seasons values (1,'2026-10-15','2026-11-18',null);
-- Cada mapa tem os mesmos 10 jogadores (p1..p5 = time A, p6..p10 = time B) e rounds = soma do placar.
create function mk(mid text, rounds int) returns void language sql as $$
  insert into matches(id, played_at, map_name, rounds_total) values (mid, '2026-10-20', mid, rounds);
  insert into player_stats select mid, 'p'||i from generate_series(1,10) i;
$$;
select mk('ma1',20), mk('ma2',18);            -- 13x7, 13x5  (2x0)
select mk('mb1',20), mk('mb2',18);            -- 13x7, 5x13  (1x1, incompleta)
select mk('mc1',20), mk('mc2',18), mk('mc3',22); -- 13x7, 13x5, 13x9 (2x0 e terceiro mapa)
select mk('md1',20), mk('md2',18), mk('md3',22); -- 13x7, 5x13, 13x9 (2x1)
select mk('me1',20);                          -- BO3 com um mapa
select mk('mf1',20);                          -- BO1
select mk('mg1',20), mk('mg2',18), mk('mg3',22), mk('mg4',20); -- 4 mapas
