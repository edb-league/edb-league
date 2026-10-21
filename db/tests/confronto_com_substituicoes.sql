-- Teste da migração 20261021_confronto_com_substituicoes.sql em um Postgres descartável (NÃO rode no Supabase).
-- Uso: crie um banco vazio, rode este arquivo, depois a migração, depois os cenários do final.
-- Esquema mínimo + dados do cenário: 3 mapas, com p5 fora e p11 dentro (time A) no mapa 2.
create schema auth;
create function auth.role() returns text language sql as $$ select 'service_role'::text $$;
create table league_seasons(number int primary key, starts_on date, ends_on date, homologated_at timestamptz);
create table matches(id text primary key, played_at date, map_name text, rounds_total int, team_a_name text, team_b_name text, team_a_score int, team_b_score int, result_verified bool);
create table player_stats(match_id text references matches(id), player_id text, won bool, primary key(match_id, player_id));
create table bo3_series(id text primary key, season_number int references league_seasons(number), sequence_number int, played_on date, team_a_name text, team_b_name text, status text, winner_side text, match_format text, notes text, unique(season_number, sequence_number));
create table bo3_maps(series_id text references bo3_series(id) on delete cascade, match_id text unique references matches(id), map_number int, winner_side text, primary key(series_id, map_number));
create table bo3_players(series_id text references bo3_series(id) on delete cascade, player_id text, team_side text check (team_side in ('a','b')), primary key(series_id, player_id));
insert into league_seasons values (1,'2026-10-19','2026-11-18',null);
-- 3 mapas; cada um com 10 jogadores. Mapa 2 tem p5 fora e p11 dentro (time A); mapa 3 volta p5 e sai p11.
insert into matches select 'm'||i, '2026-10-20', 'Map'||i, case when i=3 then 21 else 20 end from generate_series(1,3) i;
insert into player_stats select 'm1', 'p'||i from generate_series(1,10) i;
insert into player_stats select 'm2', 'p'||i from generate_series(1,10) i where i<>5;
insert into player_stats values ('m2','p11');
insert into player_stats select 'm3', 'p'||i from generate_series(1,10) i;

-- Cenário esperado (depois de aplicar a migração):
-- select register_edb_confronto('{"season_number":1,"format":"bo3","team_a_name":"PT","team_b_name":"PL",
--   "team_a_player_ids":["p1","p2","p3","p4","p5"],"matches":[
--   {"match_id":"m1","team_a_score":13,"team_b_score":7,"team_a_player_ids":["p1","p2","p3","p4","p5"]},
--   {"match_id":"m2","team_a_score":7,"team_b_score":13,"team_a_player_ids":["p1","p2","p3","p4","p11"]},
--   {"match_id":"m3","team_a_score":13,"team_b_score":8,"team_a_player_ids":["p1","p2","p3","p4","p5"]}]}'::jsonb);
-- Resultado: bo3_players com 6 no lado a (p1..p5 e p11) e 5 no lado b; em m2, p11 com won=false e p6..p10 com won=true.
-- Também testados: formato antigo sem lista por mapa; BO1; jogador nos dois times (recusado); lista com 4 jogadores
-- (recusada); time A que não confere com o mapa (recusado); mapa já vinculado (recusado).
