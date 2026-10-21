-- Cenários da migração 20261021_md3_dois_mapas.sql. Rode depois da migração; qualquer falha levanta erro.
create function reg(fmt text, maps jsonb) returns text language plpgsql as $$
begin
  return register_edb_confronto(jsonb_build_object('season_number',1,'format',fmt,'team_a_name','PT','team_b_name','PL',
    'team_a_player_ids','["p1","p2","p3","p4","p5"]'::jsonb,'matches',maps))::text;
exception when others then return 'ERRO: '||sqlerrm;
end $$;
create function m(mid text, a int, b int) returns jsonb language sql as $$
  select jsonb_build_object('match_id',mid,'team_a_score',a,'team_b_score',b) $$;
do $$
declare r text;
begin
  r := reg('bo3', jsonb_build_array(m('ma1',13,7), m('ma2',13,5)));
  if r like 'ERRO%' or (r::jsonb->>'map_count')<>'2' or (r::jsonb->>'winner_side')<>'a' then raise exception '2x0: %', r; end if;
  r := reg('bo3', jsonb_build_array(m('mb1',13,7), m('mb2',5,13)));
  if r not like 'ERRO: BO3 incompleta: placar 1x1%' then raise exception '1x1 deveria falhar: %', r; end if;
  r := reg('bo3', jsonb_build_array(m('mc1',13,7), m('mc2',13,5), m('mc3',13,9)));
  if r not like 'ERRO: A serie ja estava decidida em 2x0 depois do mapa 2%' then raise exception '2x0 + terceiro: %', r; end if;
  r := reg('bo3', jsonb_build_array(m('md1',13,7), m('md2',5,13), m('md3',13,9)));
  if r like 'ERRO%' or (r::jsonb->>'map_count')<>'3' or (r::jsonb->>'winner_side')<>'a' then raise exception '2x1: %', r; end if;
  r := reg('bo3', jsonb_build_array(m('me1',13,7)));
  if r not like 'ERRO: BO1 exige 1 mapa e BO3 exige 2 ou 3%' then raise exception 'BO3 com 1 mapa: %', r; end if;
  r := reg('bo1', jsonb_build_array(m('mf1',13,7)));
  if r like 'ERRO%' or (r::jsonb->>'map_count')<>'1' then raise exception 'BO1: %', r; end if;
  r := reg('bo3', jsonb_build_array(m('mg1',13,7), m('mg2',13,5), m('mg3',13,9), m('mg4',13,7)));
  if r not like 'ERRO: BO1 exige 1 mapa e BO3 exige 2 ou 3%' then raise exception '4 mapas: %', r; end if;
  -- só entraram as séries válidas
  if (select count(*) from bo3_series) <> 3 then raise exception 'esperava 3 séries'; end if;
  if (select count(*) from bo3_maps) <> 6 then raise exception 'esperava 6 mapas'; end if;
  if exists(select 1 from bo3_maps where match_id in ('mb1','mb2','mc1','mc2','mc3','me1','mg1')) then raise exception 'mapa de série recusada ficou vinculado'; end if;
  raise notice 'OK: todos os cenários passaram';
end $$;
