import Link from "next/link";
import { Card, EmptyState, SectionTitle } from "@/components/ui/Card";
import { AchievementTabs } from "@/components/layout/SectionTabs";
import { PageHeader } from "@/components/ui/PageHeader";
import { TableWrap, Td, Th } from "@/components/ui/Table";
import { api } from "@/lib/api";
import { num } from "@/lib/format";
import type { Hall, Meta, PlayerRef, RecordCard } from "@/lib/types";

export const metadata = { title: "Hall da Fama" };

function Holders({ holders }: { holders: PlayerRef[] }) {
  return (
    <>
      {holders.map((h, i) => (
        <span key={h.id}>
          {i > 0 && " · "}
          <Link href={`/jogadores/${encodeURIComponent(h.id)}`}>{h.name}</Link>
        </span>
      ))}
    </>
  );
}

function Henio({ henio }: { henio: Hall["henio"] }) {
  return (
    <div className="card flex flex-col gap-1 border-2 border-gold-bg p-4">
      <p className="kicker">Homenagem da EDB LEAGUE</p>
      <h3 className="text-lg font-bold">Prêmio Henio · jogador com pior ADR</h3>
      {henio ? (
        <>
          <p className="tabular text-3xl font-extrabold text-gold">{num(henio.adr, 1)} ADR</p>
          <p className="text-base font-bold">
            <Holders holders={henio.holders} />
          </p>
          <p className="text-sm text-muted">
            Menor ADR acumulado: dano total dividido pelos rounds de todos os mapas oficiais.
          </p>
        </>
      ) : (
        <>
          <p className="text-2xl font-extrabold">A definir</p>
          <p className="text-sm text-muted">Aguardando jogadores com ao menos 2 mapas e dano registrado.</p>
        </>
      )}
    </div>
  );
}

export default async function HallPage() {
  const [meta, hall] = await Promise.all([api<Meta>("/meta"), api<Hall>("/hall-of-fame")]);

  return (
    <>
      <PageHeader
        title="Hall da Fama"
        subtitle="Grandes jogadores constroem momentos. Lendas deixam um legado."
        art="trophy"
        counts={{ players: meta.counts.players, matches: meta.counts.matches, maps: meta.counts.maps }}
      />
      <AchievementTabs current="/hall-da-fama" />

      {hall.records.length === 0 ? (
        <EmptyState>Ainda não há estatísticas suficientes para estabelecer recordes.</EmptyState>
      ) : (
        <div className="grid grid-cols-[minmax(0,1fr)] gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,2fr)]">
          <div className="flex flex-col gap-6">
            {hall.top_kills.length > 0 && (
              <section aria-labelledby="top5">
                <SectionTitle id="top5" title="Top 5: kills acumuladas" />
                <ol className="card divide-y divide-line-soft">
                  {hall.top_kills.map((t, i) => (
                    <li key={t.player.id} className="flex items-center justify-between gap-3 px-4 py-2 text-base">
                      <span>
                        <b className="tabular mr-3 text-gold">{i + 1}.</b>
                        <Link href={`/jogadores/${encodeURIComponent(t.player.id)}`}>{t.player.name}</Link>
                      </span>
                      <b className="tabular">{num(t.kills)} kills</b>
                    </li>
                  ))}
                </ol>
              </section>
            )}
            <Henio henio={hall.henio} />
          </div>

          <section aria-labelledby="recordes">
            <SectionTitle id="recordes" title="Recordes da EDB LEAGUE" />
            <ul className="grid gap-3 sm:grid-cols-2">
              {hall.records.map((r) => (
                <li key={r.title} className="card flex flex-col gap-1 p-4">
                  <h3 className="text-base font-bold text-muted">{r.title}</h3>
                  <p className="tabular text-2xl font-extrabold text-gold">{r.value}</p>
                  <p className="text-base font-bold">
                    <Holders holders={r.holders} />
                  </p>
                  {r.detail.length > 90 ? (
                    <details className="text-sm text-muted">
                      <summary className="cursor-pointer">Ver as partidas</summary>
                      <p className="mt-1">{r.detail}</p>
                    </details>
                  ) : (
                    <p className="text-sm text-muted">{r.detail}</p>
                  )}
                </li>
              ))}
            </ul>
            <p className="mt-3 text-sm text-muted">
              Recordes calculados pelas partidas registradas e dados disponíveis no SCOPE.GG. K/D geral exige ao menos
              duas partidas.
            </p>
          </section>
        </div>
      )}

      <Card aria-labelledby="campeoes">
        <SectionTitle id="campeoes" title="Campeões oficiais por temporada" />
        {hall.titles.length ? (
          <TableWrap caption="Campeões oficiais por temporada">
            <thead>
              <tr>
                <Th>Temporada</Th>
                <Th>Título</Th>
                <Th>Jogador</Th>
                <Th numeric>Pontuação</Th>
              </tr>
            </thead>
            <tbody>
              {hall.titles.map((t) => (
                <tr key={`${t.season_number}-${t.title}`}>
                  <Td>{t.season_number}</Td>
                  <Td className="font-bold">{t.title}</Td>
                  <Td>
                    {t.player ? (
                      <Link href={`/jogadores/${encodeURIComponent(t.player.id)}`}>{t.player.name}</Link>
                    ) : (
                      "Não identificado"
                    )}
                  </Td>
                  <Td numeric>{num(t.score, 2)}</Td>
                </tr>
              ))}
            </tbody>
          </TableWrap>
        ) : (
          <p className="text-base text-muted">A primeira premiação oficial será homologada após a Temporada 1.</p>
        )}
      </Card>
    </>
  );
}
