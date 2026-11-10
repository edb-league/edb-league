-- Amplia a escala de nível dos jogadores (usada só no Sorteador) de 1–10 para 1–15.
alter table public.players drop constraint if exists players_skill_level_check;
alter table public.players add constraint players_skill_level_check check (skill_level between 1 and 15);
