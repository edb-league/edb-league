import clsx from "clsx";
import Link from "next/link";
import { notFound } from "next/navigation";
import { RankingList } from "@/components/rankings/RankingList";
import { SeasonBar } from "@/components/layout/SeasonBar";
import { Card, SectionTitle } from "@/components/ui/Card";
import { PageHeader } from "@/components/ui/PageHeader";
import { TableWrap, Td, Th } from "@/components/ui/Table";
import { api, qs } from "@/lib/api";
import { num, seasonQuery, signed } from "@/lib/format";
import { seasonContext } from "@/lib/season";
import type { Ranking, RankingType } from "@/lib/types";

const TABS: { type: RankingType; label: string }[] = [
  { type: "elite", label: "Elite" },
  { type: "superacao", label: "Superação" },
  { type: "bagres", label: "BAGRES" },
];

export async function generateMetadata({ params }: { params: Promise<{ tipo: string }> }) {
  const { tipo } = await params;
  const tab = TABS.find((t) => t.type === tipo);
  return { title: tab ? `Ranking ${tab.label}` : "Rankings" };
}

export default async function RankingPage({
  params,
  searchParams,
}: {
  params: Promise<{ tipo: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { tipo } = await params;
  const valid = ["elite", "superacao", "bagres", "xp"];
  if (!valid.includes(tipo)) notFound();
  const type = tipo as RankingType;
  const { meta, season } = await seasonContext((await searchParams).temporada);
  const ranking = await api<Ranking>(`/rankings/${type}${qs({ season })}`);

  return (
    <>
      <PageHeader
        title="Rankings da EDB LEAGUE"
        subtitle="Desempenho Elite, superação pessoal e o ranking BAGRES, pior ADR primeiro."
        art="rankings"
        counts={{ players: meta.counts.players, matches: meta.counts.matches, maps: meta.counts.maps }}
      />
      <SeasonBar meta={meta} season={season} path={`/rankings/${type}`} />

      <nav aria-label="Tipo de ranking">
        <ul className="flex flex-wrap gap-2">
          {TABS.map((tab) => {
            const active = tab.type === type;
            return (
              <li key={tab.type}>
                <Link
                  href={`/rankings/${tab.type}${seasonQuery(season)}`}
                  aria-current={active ? "page" : undefined}
                  className={clsx(
                    "inline-flex min-h-11 items-center rounded-lg border px-5 text-base font-bold no-underline",
                    active ? "border-gold-bg bg-gold-bg text-on-gold" : "border-line bg-surface text-fg hover:bg-surface-2",
                  )}
                >
                  {tab.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <section aria-labelledby="ranking-titulo">
        <SectionTitle id="ranking-titulo" title={ranking.title}>
          {ranking.notes[0]}
        </SectionTitle>
        <RankingList ranking={ranking} />
      </section>

      {ranking.notes.length > 1 && (
        <Card>
          <details>
            <summary className="cursor-pointer text-lg font-bold">Como funciona este ranking</summary>
            <div className="mt-3 flex max-w-prose flex-col gap-2 text-base text-muted">
              {ranking.notes.slice(1).map((note) => (
                <p key={note}>{note}</p>
              ))}
            </div>
          </details>
        </Card>
      )}

      {ranking.type === "superacao" && (
        <section aria-labelledby="evolucao">
          <SectionTitle id="evolucao" title="Evolução real: últimas 2 partidas contra as 2 anteriores" />
          {ranking.progress && ranking.progress.length > 0 ? (
            <TableWrap caption="Evolução do KPR, últimas duas partidas contra as duas anteriores">
              <thead>
                <tr>
                  <Th>Jogador</Th>
                  <Th numeric>Evolução</Th>
                  <Th numeric>Jogos</Th>
                </tr>
              </thead>
              <tbody>
                {ranking.progress.map((row) => (
                  <tr key={row.name}>
                    <Td>{row.name}</Td>
                    <Td numeric>{signed(row.change_pct, 1, "%")}</Td>
                    <Td numeric>{num(row.games)}</Td>
                  </tr>
                ))}
              </tbody>
            </TableWrap>
          ) : (
            <p className="text-base text-muted">Precisamos de pelo menos quatro partidas por jogador para medir evolução histórica.</p>
          )}
        </section>
      )}
    </>
  );
}
