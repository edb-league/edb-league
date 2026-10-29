import { MapCardItem, MapRowItem, SeriesCardItem } from "@/components/matches/Cards";
import { SeasonBar } from "@/components/layout/SeasonBar";
import { EmptyState, SectionTitle } from "@/components/ui/Card";
import { Fmt } from "@/components/ui/MapTile";
import { PageHeader } from "@/components/ui/PageHeader";
import { api, qs } from "@/lib/api";
import { first, seasonQuery } from "@/lib/format";
import { seasonContext } from "@/lib/season";
import type { MatchesList, SeriesCard } from "@/lib/types";

export const metadata = { title: "Partidas" };

export default async function MatchesPage({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const sp = await searchParams;
  const { meta, season } = await seasonContext(sp.temporada);
  const list = await api<MatchesList>(`/matches${qs({ season })}`);
  const selectedId = first(sp.confronto);
  const all: SeriesCard[] = [...list.bo1, ...list.bo3];
  const selected = all.find((s) => s.id === selectedId) ?? null;

  const seriesHref = (s: SeriesCard) =>
    s.id === selected?.id ? `/partidas${seasonQuery(season)}` : `/partidas${seasonQuery(season, { confronto: s.id })}#confronto-${s.id}`;
  const mapHref = (id: string, confronto?: string) =>
    `/partidas/mapa/${encodeURIComponent(id)}${seasonQuery(season, { confronto })}`;

  return (
    <>
      <PageHeader
        title="Histórico de partidas"
        subtitle="BO1 e BO3: cada mapa conta igualmente na temporada."
        art="matches"
      >
        <SeasonBar meta={meta} season={season} path="/partidas" variant="strip" />
      </PageHeader>

      <div className="grid gap-8 lg:grid-cols-2">
        {(
          [
            ["BO1", "Partidas avulsas", list.bo1],
            ["BO3", "Séries de três mapas", list.bo3],
          ] as const
        ).map(([label, description, items]) => (
          <section key={label} aria-labelledby={`grupo-${label}`}>
            <SectionTitle id={`grupo-${label}`} title={<><Fmt format={label} /> · {items.length}</>}>
              {description}
            </SectionTitle>
            {items.length ? (
              <ul className="flex flex-col gap-3">
                {items.map((s) => (
                  <SeriesCardItem key={s.id} series={s} href={seriesHref(s)} active={s.id === selected?.id}>
                    {s.maps.length ? (
                      <ul className="flex flex-col gap-2" aria-label={`Mapas desta ${s.format.toUpperCase()}`}>
                        {s.maps.map((m) => (
                          <MapRowItem key={m.id} card={m} href={mapHref(m.id, s.id)} />
                        ))}
                      </ul>
                    ) : (
                      <EmptyState>
                        Este confronto ainda não tem mapas vinculados. Os registros serão adicionados após a conferência dos prints.
                      </EmptyState>
                    )}
                  </SeriesCardItem>
                ))}
              </ul>
            ) : (
              <EmptyState>Nenhuma {label} nesta temporada.</EmptyState>
            )}
          </section>
        ))}
      </div>

      {list.legacy.length > 0 && (
        <details className="card p-4">
          <summary className="cursor-pointer text-lg font-bold">
            Mapas antigos ainda não agrupados ({list.legacy.length})
          </summary>
          <p className="mt-2 text-base text-muted">
            Registros preservados. Vincule os mapas a BO1 ou BO3 na Administração após conferir os placares.
          </p>
          <ul className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {list.legacy.map((m) => (
              <MapCardItem key={m.id} card={m} href={mapHref(m.id)} />
            ))}
          </ul>
        </details>
      )}
    </>
  );
}
