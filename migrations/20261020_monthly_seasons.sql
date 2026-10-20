-- EDB LEAGUE: temporadas mensais iniciadas todo dia 19, a partir de 19/10/2026.
-- Preserva resultados, jogadores, estrelas congeladas, títulos e a Temporada 0.
-- O banco usa a data de Brasília para determinar a temporada vigente.

DO $guard$
BEGIN
 IF EXISTS (
  SELECT 1 FROM public.league_seasons s
  WHERE s.number>=1 AND s.homologated_at IS NOT NULL
    AND (
      s.starts_on IS DISTINCT FROM
        (DATE '2026-10-19' + (s.number-1)*INTERVAL '1 month')::date
      OR s.ends_on IS DISTINCT FROM
        ((DATE '2026-10-19' + s.number*INTERVAL '1 month')::date-1)
    )
 ) THEN
   RAISE EXCEPTION 'Existe temporada homologada com datas antigas; revisar antes de migrar';
 END IF;
 IF EXISTS (
  SELECT 1
  FROM public.bo3_series b
  JOIN public.bo3_maps bm ON bm.series_id=b.id
  JOIN public.matches m ON m.id=bm.match_id
  WHERE b.season_number>=1 AND
    (m.played_at < (DATE '2026-10-19' + (b.season_number-1)*INTERVAL '1 month')::date
     OR m.played_at > (DATE '2026-10-19' + b.season_number*INTERVAL '1 month')::date-1)
 ) THEN
   RAISE EXCEPTION 'Ha partidas associadas a temporadas fora do novo periodo mensal';
 END IF;
END $guard$;

-- Atualiza a Temporada 1 e as temporadas futuras já criadas, sem mexer nas homologadas.
UPDATE public.league_seasons s
SET starts_on=(DATE '2026-10-19' + (s.number-1)*INTERVAL '1 month')::date,
    ends_on=(DATE '2026-10-19' + s.number*INTERVAL '1 month')::date-1
WHERE s.number>=1 AND s.homologated_at IS NULL
  AND (
    s.starts_on IS DISTINCT FROM
       (DATE '2026-10-19' + (s.number-1)*INTERVAL '1 month')::date
    OR s.ends_on IS DISTINCT FROM
       ((DATE '2026-10-19' + s.number*INTERVAL '1 month')::date-1)
  );

CREATE OR REPLACE FUNCTION public.ensure_edb_calendar()
RETURNS integer
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO 'public'
AS $function$
DECLARE
  v_day date := (now() AT TIME ZONE 'America/Sao_Paulo')::date;
  v_current integer := 0;
  v_last integer;
  v_reference date;
BEGIN
  IF v_day >= DATE '2026-10-19' THEN
    -- Subtrair 18 dias faz a virada do mes civil cair sempre no dia 19.
    -- Ex.: 18/11 -> outubro (T1), 19/11 -> novembro (T2).
    v_reference := v_day - 18;
    v_current := 1 + 12*(extract(year FROM v_reference)::integer - 2026)
                   + extract(month FROM v_reference)::integer - 10;
  END IF;
  -- Mantém preparada também a próxima temporada.
  v_last := greatest(v_current+1,2);

  INSERT INTO public.league_seasons(number,label,starts_on,ends_on,bo3_target)
  SELECT i,'Temporada '||i,
    (DATE '2026-10-19' + (i-1)*INTERVAL '1 month')::date,
    (DATE '2026-10-19' + i*INTERVAL '1 month')::date-1,
    NULL::integer
  FROM generate_series(1,v_last) AS i
  ON CONFLICT (number) DO NOTHING;

  IF v_current >= 1 THEN
    INSERT INTO public.season_player_stars(season_number,player_id,stars)
    SELECT v_current,id,stars FROM public.players
    ON CONFLICT DO NOTHING;
  END IF;
  RETURN v_current;
END
$function$;

-- O gatilho de jogadores também precisa usar o calendário novo.
-- Assim uma edição de nível/estrelas não congelará estrelas na temporada errada.
CREATE OR REPLACE FUNCTION public.freeze_current_stars_on_player_change()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO 'public'
AS $function$
DECLARE
  v_day date := (now() AT TIME ZONE 'America/Sao_Paulo')::date;
  v_num integer;
BEGIN
  IF v_day < DATE '2026-10-19' THEN
    RETURN NEW;
  END IF;
  v_num := public.ensure_edb_calendar();
  INSERT INTO public.season_player_stars(season_number,player_id,stars)
  VALUES (
    v_num,NEW.id,
    CASE WHEN TG_OP='UPDATE' THEN OLD.stars ELSE NEW.stars END
  )
  ON CONFLICT DO NOTHING;
  RETURN NEW;
END
$function$;

-- Confirma a temporada atual sem sobrescrever estrelas previamente congeladas.
SELECT public.ensure_edb_calendar();
