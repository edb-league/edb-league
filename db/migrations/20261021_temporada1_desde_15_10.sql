-- Temporada 1 passa a começar em 15/10/2026, data da primeira demo da liga.
-- Só ajusta a data de início; o fim (18/11) e a Temporada 2 não mudam.
-- ensure_edb_calendar() insere com ON CONFLICT DO NOTHING, então não sobrescreve esta data.
DO $guard$
BEGIN
  IF EXISTS (SELECT 1 FROM public.league_seasons WHERE number=1 AND homologated_at IS NOT NULL) THEN
    RAISE EXCEPTION 'Temporada 1 ja homologada; nao alterar o inicio';
  END IF;
END $guard$;

UPDATE public.league_seasons SET starts_on = DATE '2026-10-15'
WHERE number = 1 AND homologated_at IS NULL;
