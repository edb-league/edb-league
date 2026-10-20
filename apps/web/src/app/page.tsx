import Image from "next/image";
import Link from "next/link";
import { TeamDraw } from "@/components/home/TeamDraw";
import { SeasonBar } from "@/components/layout/SeasonBar";
import { Card, EmptyState, SectionTitle } from "@/components/ui/Card";
import { BarList } from "@/components/ui/Charts";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatGrid, Stat } from "@/components/ui/Stat";
import { api, qs } from "@/lib/api";
import { num, seasonQuery } from "@/lib/format";
import { seasonContext } from "@/lib/season";
import type { Home } from "@/lib/types";

export const metadata = { title: "Visão geral" };

const RANKING_NAME = { elite: "Ranking Elite", superacao: "Ranking Superação", xp: "Ranking XP" } as const;

export default async function HomePage({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const { meta, season } = await seasonContext((await searchParams).temporada);
  const home = await api<Home>(`/home${qs({ season })}`);

  return (
    <>
      <PageHeader
        title="Os Xinxas agora têm ranking."
        subtitle="Cada frag conta. Cada evolução importa. A temporada começa aqui."
        art="home"
        counts={{ players: meta.counts.players, matches: meta.counts.matches, maps: meta.counts.maps }}
      />
      <SeasonBar meta={meta} season={season} path="/" />

      <section aria-labelledby="numeros">
        <h2 id="numeros" className="sr-only">Números da temporada</h2>
        <StatGrid>
          <Stat label="Jogadores ativos" value={num(home.counts.players)} />
          <Stat label="Partidas registradas" value={num(home.counts.matches)} />
          <Stat label="Kills registradas" value={num(home.counts.kills)} />
          <Stat label="XP distribuído" value={num(home.counts.xp_distributed)} />
        </StatGrid>
      </section>

      <section aria-labelledby="destaques">
        <SectionTitle id="destaques" title="Destaques da temporada" />
        <ul className="grid gap-4 md:grid-cols-3">
          {home.highlights.map((h) => (
            <li key={h.title} className="card p-5">
              <p className="kicker">
                {h.title} · {RANKING_NAME[h.ranking]}
              </p>
              <p className="mt-2 text-2xl font-bold break-words">
                {h.player ? (
                  <Link href={`/jogadores/${encodeURIComponent(h.player.id)}`}>{h.player.name}</Link>
                ) : (
                  "A definir"
                )}
              </p>
              <p className="mt-1 text-base text-muted">{h.detail}</p>
            </li>
          ))}
        </ul>
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card aria-labelledby="elite-titulo">
          <SectionTitle id="elite-titulo" kicker="Disputa da temporada" title="Classificação Elite">
            Os líderes do índice Elite com base no desempenho dos mapas da temporada.
          </SectionTitle>
          {home.top_elite.length ? (
            <BarList
              caption="Dez primeiros do ranking Elite, índice de desempenho"
              items={home.top_elite.map((r) => ({
                id: r.player_id,
                label: r.name,
                value: r.elite,
                href: `/jogadores/${encodeURIComponent(r.player_id)}`,
              }))}
            />
          ) : (
            <EmptyState>O ranking será exibido após o registro das primeiras partidas.</EmptyState>
          )}
          <p className="mt-4 text-sm text-muted">
            Índice de desempenho (KPR + ADR). Classificação provisória até a homologação; são necessários 6 mapas para
            concorrer aos títulos oficiais.
          </p>
          <p className="mt-3">
            <Link href={`/rankings/elite${seasonQuery(season)}`} className="inline-flex min-h-11 items-center text-base font-bold">
              Ver ranking completo →
            </Link>
          </p>
        </Card>

        <Card aria-labelledby="homenagem-titulo" className="flex flex-col">
          <SectionTitle id="homenagem-titulo" kicker="Marco histórico · EDB LEAGUE" title="Inaugurada na gestão do Presidente Dudu" />
          <div className="relative mx-auto aspect-[4/5] w-full max-w-sm overflow-hidden rounded-lg border border-line-soft bg-surface-2">
            <Image
              src="/president.avif"
              alt="Retrato cerimonial do Presidente Dudu no Elenco de Bosta"
              fill
              sizes="(min-width: 1024px) 24rem, 90vw"
              className="object-contain"
            />
          </div>
          <p className="mt-4 text-center text-lg font-bold text-gold">19 de outubro de 2026</p>
        </Card>
      </div>

      <Card aria-labelledby="sorteador">
        <SectionTitle id="sorteador" kicker="Partida 5 × 5" title="Sorteador de times">
          Divisão automática usando os níveis de 1 a 10 cadastrados na EDB LEAGUE.
        </SectionTitle>
        <TeamDraw roster={home.roster} />
      </Card>

      <Card aria-labelledby="regras">
        <p className="kicker mb-1">Regulamento · EDB LEAGUE</p>
        <h2 id="regras" className="text-2xl font-bold">Como funcionam as temporadas?</h2>
        <p className="mt-2 max-w-prose text-base text-muted">
          A cada temporada, uma nova disputa começa e os rankings são reiniciados. Jogue quantas vezes quiser,
          acompanhe sua evolução e tente conquistar as primeiras posições. Cada novo mapa pode melhorar sua
          classificação.
        </p>
        <dl className="mt-4 grid gap-3 md:grid-cols-3">
          <Stat label="Duração" value="1 mês" hint="Do dia 19 ao dia 18 do mês seguinte" />
          <Stat label="Confrontos" value="BO1 e BO3 livres" hint="Sem limite de confrontos ou mapas por temporada" />
          <Stat label="Pontuação" value="Top 6 mapas" hint="Os 6 melhores mapas de cada jogador contam em cada ranking" />
        </dl>
        <p className="mt-4 max-w-prose text-base text-muted">
          Para concorrer aos títulos, é necessário disputar pelo menos 6 mapas. Ao final da temporada, os líderes dos
          rankings Elite, Superação e XP poderão conquistar os títulos de MVP, Revelação e Xinxa. Todos os resultados
          ficam registrados no histórico da liga.
        </p>
      </Card>
    </>
  );
}
