-- BO3 pode terminar 2x0 (dois mapas) ou 2x1 (três mapas).
--
-- Antes: register_edb_confronto exigia exatamente 3 mapas em BO3.
-- Agora: BO3 aceita 2 ou 3 mapas. Com 2 mapas o mesmo time precisa ter vencido os dois (2x0);
-- com 3 mapas, nenhum time pode ter 2 vitorias antes do terceiro (2x1). BO1 continua com 1 mapa.
-- Mantem tudo da versao anterior (substituicoes por mapa, 10 jogadores distintos, placar somando os rounds, etc.).
-- Nao altera dados existentes: so substitui a funcao.

CREATE OR REPLACE FUNCTION public.register_edb_confronto(p_bundle jsonb)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE
  v_season integer;
  v_format text;
  v_expected integer;
  v_team_a text;
  v_team_b text;
  v_a_ids text[];
  v_match_a text[];
  v_all_a text[] := '{}';
  v_all_b text[] := '{}';
  v_item jsonb;
  v_mid text;
  v_a_score integer;
  v_b_score integer;
  v_map_winner text;
  v_a_wins integer := 0;
  v_b_wins integer := 0;
  v_i integer := 0;
  v_number integer;
  v_series text := gen_random_uuid()::text;
  v_first_date date;
  v_start date;
  v_end date;
  v_homologated timestamptz;
  v_winner text;
  v_actual_roster text[];
  v_existing_score record;
BEGIN
  IF auth.role() IS DISTINCT FROM 'service_role' THEN
    RAISE EXCEPTION 'Somente a administracao da liga pode registrar confrontos';
  END IF;
  IF p_bundle IS NULL OR jsonb_typeof(p_bundle) <> 'object' THEN
    RAISE EXCEPTION 'Pacote de confronto invalido';
  END IF;
  v_format := lower(p_bundle->>'format');
  IF v_format NOT IN ('bo1','bo3') OR v_format IS NULL THEN
    RAISE EXCEPTION 'Selecione BO1 ou BO3';
  END IF;
  IF jsonb_typeof(p_bundle->'matches') IS DISTINCT FROM 'array' THEN
    RAISE EXCEPTION 'Informe a lista de mapas do confronto';
  END IF;
  v_expected := jsonb_array_length(p_bundle->'matches');
  IF (v_format='bo1' AND v_expected<>1) OR (v_format='bo3' AND v_expected NOT IN (2,3)) THEN
    RAISE EXCEPTION 'BO1 exige 1 mapa e BO3 exige 2 ou 3 mapas (recebidos: %)',v_expected;
  END IF;
  IF jsonb_typeof(p_bundle->'team_a_player_ids') IS DISTINCT FROM 'array'
     OR jsonb_array_length(p_bundle->'team_a_player_ids') <> 5 THEN
    RAISE EXCEPTION 'Selecione exatamente cinco jogadores do time A';
  END IF;
  SELECT array_agg(value) INTO v_a_ids
  FROM jsonb_array_elements_text(p_bundle->'team_a_player_ids') AS a(value);
  IF (SELECT count(DISTINCT x) FROM unnest(v_a_ids) x) <> 5 THEN
    RAISE EXCEPTION 'Ha jogadores repetidos no time A';
  END IF;
  v_team_a := btrim(coalesce(p_bundle->>'team_a_name',''));
  v_team_b := btrim(coalesce(p_bundle->>'team_b_name',''));
  IF length(v_team_a) NOT BETWEEN 1 AND 40 OR length(v_team_b) NOT BETWEEN 1 AND 40
    OR lower(v_team_a)=lower(v_team_b) THEN
    RAISE EXCEPTION 'Informe nomes distintos e validos para os dois times';
  END IF;
  v_season := (p_bundle->>'season_number')::integer;
  IF v_season IS NULL OR v_season < 1 THEN
    RAISE EXCEPTION 'Confrontos novos sao permitidos apenas a partir da Temporada 1';
  END IF;

  -- Serializa gravacoes por temporada e protege contra homologacao simultanea.
  PERFORM pg_advisory_xact_lock(hashtext('edb_confronto_'||v_season));
  SELECT starts_on,ends_on,homologated_at INTO v_start,v_end,v_homologated
  FROM public.league_seasons WHERE number=v_season FOR UPDATE;
  IF NOT FOUND OR v_start IS NULL OR v_end IS NULL OR v_homologated IS NOT NULL THEN
    RAISE EXCEPTION 'Temporada inexistente, sem calendario ou ja homologada';
  END IF;
  SELECT coalesce(max(sequence_number),0)+1 INTO v_number
  FROM public.bo3_series WHERE season_number=v_season;

  FOR v_item IN SELECT value FROM jsonb_array_elements(p_bundle->'matches') LOOP
    v_i := v_i + 1;
    v_mid := btrim(coalesce(v_item->>'match_id',''));
    IF v_mid='' THEN RAISE EXCEPTION 'Mapa sem identificador'; END IF;
    -- Bloqueia o mapa, impedindo uma segunda vinculacao concorrente.
    SELECT played_at,rounds_total,team_a_score,team_b_score
    INTO v_existing_score FROM public.matches WHERE id=v_mid FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'Mapa nao encontrado: %',v_mid; END IF;
    IF EXISTS(SELECT 1 FROM public.bo3_maps WHERE match_id=v_mid) THEN
      RAISE EXCEPTION 'Mapa % ja pertence a um confronto',v_mid;
    END IF;
    IF v_existing_score.played_at<v_start OR v_existing_score.played_at>v_end THEN
      RAISE EXCEPTION 'Mapa % nao pertence ao calendario da temporada',v_mid;
    END IF;
    IF v_first_date IS NULL THEN v_first_date:=v_existing_score.played_at; END IF;
    v_a_score := (v_item->>'team_a_score')::integer;
    v_b_score := (v_item->>'team_b_score')::integer;
    IF v_a_score IS NULL OR v_b_score IS NULL OR
      v_a_score<0 OR v_b_score<0 OR v_a_score=v_b_score THEN
      RAISE EXCEPTION 'Placar invalido do mapa %',v_mid;
    END IF;
    IF v_existing_score.rounds_total IS NOT NULL AND
      v_a_score+v_b_score<>v_existing_score.rounds_total THEN
      RAISE EXCEPTION 'O placar do mapa % nao soma os % rounds informados',
        v_mid,v_existing_score.rounds_total;
    END IF;
    SELECT array_agg(player_id ORDER BY player_id) INTO v_actual_roster
    FROM public.player_stats WHERE match_id=v_mid;
    IF array_length(v_actual_roster,1) IS DISTINCT FROM 10
      OR (SELECT count(DISTINCT r) FROM unnest(v_actual_roster) r)<>10 THEN
      RAISE EXCEPTION 'O mapa % precisa de 10 jogadores distintos',v_mid;
    END IF;
    -- Time A deste mapa: lista propria do mapa (substituicoes) ou a da serie.
    IF jsonb_typeof(v_item->'team_a_player_ids') = 'array' THEN
      SELECT array_agg(value) INTO v_match_a
      FROM jsonb_array_elements_text(v_item->'team_a_player_ids') AS a(value);
      IF array_length(v_match_a,1) IS DISTINCT FROM 5
        OR (SELECT count(DISTINCT x) FROM unnest(v_match_a) x)<>5 THEN
        RAISE EXCEPTION 'O time A do mapa % precisa de cinco jogadores distintos',v_mid;
      END IF;
    ELSE
      v_match_a := v_a_ids;
    END IF;
    IF (SELECT count(*) FROM unnest(v_match_a) a
        WHERE a=ANY(v_actual_roster))<>5 THEN
      RAISE EXCEPTION 'Jogadores do time A nao conferem com o mapa %',v_mid;
    END IF;
    -- Ninguem joga pelos dois times na mesma serie.
    IF EXISTS(SELECT 1 FROM unnest(v_actual_roster) r
              WHERE NOT (r=ANY(v_match_a)) AND r=ANY(v_all_a))
      OR EXISTS(SELECT 1 FROM unnest(v_match_a) a WHERE a=ANY(v_all_b)) THEN
      RAISE EXCEPTION 'Um jogador aparece nos dois times da mesma serie (mapa %)',v_mid;
    END IF;
    v_all_a := ARRAY(SELECT DISTINCT x FROM unnest(v_all_a || v_match_a) x);
    v_all_b := ARRAY(SELECT DISTINCT x FROM unnest(v_all_b ||
      ARRAY(SELECT r FROM unnest(v_actual_roster) r WHERE NOT (r=ANY(v_match_a)))) x);
    -- Impede que um mesmo mapa seja enviado mais de uma vez no mesmo pacote.
    IF EXISTS(SELECT 1 FROM jsonb_array_elements(p_bundle->'matches') a
              WHERE a->>'match_id'=v_mid
              HAVING count(*)>1) THEN
      RAISE EXCEPTION 'Mapa duplicado: %',v_mid;
    END IF;
    v_map_winner := CASE WHEN v_a_score>v_b_score THEN 'a' ELSE 'b' END;
    IF v_map_winner='a' THEN v_a_wins:=v_a_wins+1;
    ELSE v_b_wins:=v_b_wins+1; END IF;
    IF v_format='bo3' AND v_i<v_expected AND (v_a_wins=2 OR v_b_wins=2) THEN
      RAISE EXCEPTION 'A serie ja estava decidida em 2x0 depois do mapa %',v_i;
    END IF;
  END LOOP;
  IF v_format='bo3' AND v_a_wins<>2 AND v_b_wins<>2 THEN
    RAISE EXCEPTION 'BO3 incompleta: placar %x% depois de % mapa(s)',v_a_wins,v_b_wins,v_expected;
  END IF;
  v_winner:=CASE WHEN v_a_wins>v_b_wins THEN 'a' ELSE 'b' END;
  INSERT INTO public.bo3_series
    (id,season_number,sequence_number,played_on,team_a_name,team_b_name,
     status,winner_side,match_format,notes)
  VALUES
    (v_series,v_season,v_number,v_first_date,v_team_a,v_team_b,
     'completed',v_winner,v_format,
     'Confronto '||upper(v_format)||' registrado pela administracao. Estatisticas por mapa.');
  INSERT INTO public.bo3_players(series_id,player_id,team_side)
  SELECT v_series,x,'a' FROM unnest(v_all_a) x
  UNION ALL
  SELECT v_series,x,'b' FROM unnest(v_all_b) x;
  v_i:=0;
  FOR v_item IN SELECT value FROM jsonb_array_elements(p_bundle->'matches') LOOP
    v_i:=v_i+1;
    v_mid:=v_item->>'match_id';
    v_a_score:=(v_item->>'team_a_score')::integer;
    v_b_score:=(v_item->>'team_b_score')::integer;
    v_map_winner:=CASE WHEN v_a_score>v_b_score THEN 'a' ELSE 'b' END;
    IF jsonb_typeof(v_item->'team_a_player_ids') = 'array' THEN
      SELECT array_agg(value) INTO v_match_a
      FROM jsonb_array_elements_text(v_item->'team_a_player_ids') AS a(value);
    ELSE
      v_match_a := v_a_ids;
    END IF;
    UPDATE public.matches SET
      team_a_name=v_team_a,team_b_name=v_team_b,
      team_a_score=v_a_score,team_b_score=v_b_score,result_verified=true
    WHERE id=v_mid;
    UPDATE public.player_stats SET
      won=CASE WHEN player_id=ANY(v_match_a) THEN v_map_winner='a'
               ELSE v_map_winner='b' END
    WHERE match_id=v_mid;
    INSERT INTO public.bo3_maps(series_id,match_id,map_number,winner_side)
    VALUES(v_series,v_mid,v_i,v_map_winner);
  END LOOP;
  RETURN jsonb_build_object(
    'series_id',v_series,'season_number',v_season,'sequence_number',v_number,
    'format',v_format,'winner_side',v_winner,'map_count',v_expected
  );
END
$function$;
