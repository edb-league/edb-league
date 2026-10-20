import Image from "next/image";
import Link from "next/link";
import { TeamDraw } from "@/components/home/TeamDraw";
import { SeasonBar } from "@/components/layout/SeasonBar";
import { Badge, TeamTag } from "@/components/ui/Badge";
import { Card, EmptyState, SectionTitle } from "@/components/ui/Card";
import { Progress } from "@/components/ui/Charts";
import { LevelBadge } from "@/components/ui/LevelBadge";
import { LinkButton } from "@/components/ui/Button";
import { Stat, StatGrid } from "@/components/ui/Stat";
import { TableWrap, Td, Th } from "@/components/ui/Table";
import { api, qs } from "@/lib/api";
import { num, seasonQuery } from "@/lib/format";
import { seasonContext } from "@/lib/season";
import type { Home, MatchesList, Ranking, SeriesCard } from "@/lib/types";

export const metadata = { title: "Início" };

const RANKING_NAME = { elite: "Ranking Elite", superacao: "Ranking Superação", xp: "Ranking XP" } as const;

/** Série mais recente já com placar, pela data do último mapa. */
function lastSeries(list: MatchesList): SeriesCard | null {
  const dated = [...list.bo1, ...list.bo3]
    .filter((s) => s.score_left !== null && s.score_right !== null)
    .map((s) => ({ s, date: s.maps.map((m) => m.date ?? "").sort().at(-1) ?? "" }))
    .sort((a, b) => b.date.localeCompare(a.date));
  return dated[0]?.s ?? null;
}

function LastSeries({ series, season }: { series: SeriesCard; season: number }) {
  const leftWins = series.winner === "left";
  const rightWins = series.winner === "right";
  const text = `${series.format.toUpperCase()} de ${series.date_label}: ${series.left} ${series.score_left} a ${series.score_right} ${series.right}`;
  return (
    <section aria-labelledby="ultimo" className="card flex flex-col gap-4 bg-surface/90 p-5">
      <div className="flex items-center justify-between gap-2">
        <h2 id="ultimo" className="text-base text-muted">Último confronto</h2>
        <Badge tone="accent">{series.format.toUpperCase()}</Badge>
      </div>
      <p className="sr-only">{text}</p>
      <div aria-hidden="true" className="grid grid-cols-[1fr_auto_1fr] items-center gap-3 text-center">
        <span className="flex flex-col items-center gap-1">
          <TeamTag name={series.left} />
          <span className="text-sm text-muted">{leftWins ? "✓ Vencedor" : rightWins ? "✕ Derrotado" : ""}</span>
        </span>
        <span className="num flex items-center gap-2 text-6xl leading-none">
          <span className={leftWins ? "text-win" : rightWins ? "text-loss" : ""}>{series.score_left}</span>
          <span className="text-3xl text-muted">x</span>
          <span className={rightWins ? "text-win" : leftWins ? "text-loss" : ""}>{series.score_right}</span>
        </span>
        <span className="flex flex-col items-center gap-1">
          <TeamTag name={series.right} />
          <span className="text-sm text-muted">{rightWins ? "✓ Vencedor" : leftWins ? "✕ Derrotado" : ""}</span>
        </span>
      </div>
      {series.maps.length > 0 && (
        <ul className="flex flex-wrap justify-center gap-2" aria-label="Mapas do confronto">
          {series.maps.map((m) => (
            <li key={m.id} className="rounded-lg border border-line-soft bg-surface-2 px-3 py-1 text-base">
              <span className="font-bold">{m.map}</span>
              {m.verified && (
                <span className="tabular ml-2 text-muted">
                  {m.score_left} a {m.score_right}
                </span>
              )}
            </li>
          ))}
        </ul>
      )}
      <Link href={`/partidas${seasonQuery(season, { confronto: series.id })}#mapas-do-confronto`} className="inline-flex min-h-11 items-center text-base font-bold">
        Ver mapas do confronto →
      </Link>
    </section>
  );
}

export default async function HomePage({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const { meta, season } = await seasonContext((await searchParams).temporada);
  const [home, elite, matches] = await Promise.all([
    api<Home>(`/home${qs({ season })}`),
    api<Ranking>(`/rankings/elite${qs({ season })}`),
    api<MatchesList>(`/matches${qs({ season })}`),
  ]);
  const current = meta.seasons.find((s) => s.number === season);
  const last = lastSeries(matches);
  const top = elite.rows.slice(0, 8);

  return (
    <>
      <section
        aria-labelledby="hero"
        className="relative isolate overflow-hidden rounded-[var(--radius-card)] border border-t-4 border-line-soft border-t-gold-bg bg-surface-2"
      >
        <Image src="/art/home.webp" alt="" fill priority sizes="100vw" className="-z-20 object-cover object-right" />
        <div aria-hidden="true" className="absolute inset-0 -z-10 bg-surface-2/92 lg:bg-linear-to-r lg:from-surface-2 lg:from-45% lg:via-surface-2/88 lg:to-surface-2/60" />
        <div className="grid grid-cols-[minmax(0,1fr)] items-center gap-8 px-5 py-8 md:px-10 md:py-12 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)]">
          <div>
            <p className="kicker mb-2">EDB LEAGUE · CS2</p>
            <h1 id="hero" className="text-6xl leading-none md:text-7xl">Os Xinxas agora têm ranking.</h1>
            <p className="mt-4 max-w-prose text-xl text-muted">Cada frag conta. Cada evolução importa. A temporada começa aqui.</p>
            <div className="mt-6 flex flex-wrap gap-3">
              <LinkButton href={`/rankings/elite${seasonQuery(season)}`} variant="gold">Ver o ranking</LinkButton>
              <LinkButton href={`/partidas${seasonQuery(season)}`} variant="secondary">Ver partidas</LinkButton>
            </div>
          </div>
          <div className="flex flex-col gap-4">
            {last && <LastSeries series={last} season={season} />}
            {current?.status === "active" && current.progress && (
              <div className="card bg-surface/90 p-4">
                <p className="mb-2 flex items-baseline justify-between gap-2 text-base">
                  <b>{current.label}</b>
                  <span className="text-muted">Dia {current.progress.day} de {current.progress.total_days}</span>
                </p>
                <Progress value={(100 * current.progress.day) / current.progress.total_days} label={`${current.label}: dia ${current.progress.day} de ${current.progress.total_days}`} />
              </div>
            )}
          </div>
        </div>
      </section>

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
            <li key={h.title} className={h.title === "MVP" ? "card border-2 border-gold-bg p-5" : "card p-5"}>
              <p className="kicker">
                {h.title} · {RANKING_NAME[h.ranking]}
              </p>
              <p className="num mt-2 text-4xl leading-tight break-words">
                {h.player ? (
                  <Link href={`/jogadores/${encodeURIComponent(h.player.id)}`} className="text-fg no-underline hover:underline">{h.player.name}</Link>
                ) : (
                  "A definir"
                )}
              </p>
              <p className="mt-1 text-base text-muted">{h.detail}</p>
            </li>
          ))}
        </ul>
      </section>

      <div className="grid grid-cols-[minmax(0,1fr)] gap-6 lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
        <Card aria-labelledby="elite-titulo">
          <SectionTitle id="elite-titulo" kicker="Disputa da temporada" title="Classificação Elite">
            Os líderes do índice Elite com base no desempenho dos mapas da temporada.
          </SectionTitle>
          {top.length ? (
            <TableWrap caption="Oito primeiros do ranking Elite">
              <thead>
                <tr>
                  <Th>#</Th>
                  <Th>Jogador</Th>
                  <Th>Nível</Th>
                  <Th numeric>K/D</Th>
                  <Th numeric>ADR</Th>
                  <Th numeric>Índice</Th>
                </tr>
              </thead>
              <tbody>
                {top.map((r) => (
                  <tr key={r.player_id}>
                    <Td className="num text-2xl text-muted">{r.rank}</Td>
                    <Td className="font-bold">
                      <Link href={`/jogadores/${encodeURIComponent(r.player_id)}`} className="text-fg">{r.name}</Link>
                      {r.provisional && <span className="ml-2 text-sm font-normal text-muted">provisório</span>}
                    </Td>
                    <Td><LevelBadge level={r.level} /></Td>
                    <Td numeric>{num(r.kd, 2)}</Td>
                    <Td numeric>{num(r.adr, 1)}</Td>
                    <Td numeric className="num text-2xl text-gold">{num(r.elite, 1)}</Td>
                  </tr>
                ))}
              </tbody>
            </TableWrap>
          ) : (
            <EmptyState>O ranking será exibido após o registro das primeiras partidas.</EmptyState>
          )}
          <p className="mt-4 text-base text-muted">
            Índice de desempenho (KPR + ADR). Classificação provisória até a homologação; são necessários 6 mapas para
            concorrer aos títulos oficiais.
          </p>
          <p className="mt-2">
            <Link href={`/rankings/elite${seasonQuery(season)}`} className="inline-flex min-h-11 items-center text-base font-bold">
              Ver ranking completo →
            </Link>
          </p>
        </Card>

        <Card aria-labelledby="homenagem-titulo" className="flex flex-col">
          <SectionTitle id="homenagem-titulo" kicker="Marco histórico · EDB LEAGUE" title="Inaugurada na gestão do Presidente Dudu" level={3} />
          <div className="relative mx-auto aspect-[4/5] w-full max-w-sm overflow-hidden rounded-lg border border-line-soft bg-surface-2">
            <Image
              src="/president.avif"
              alt="Retrato cerimonial do Presidente Dudu no Elenco de Bosta"
              fill
              sizes="(min-width: 1024px) 24rem, 90vw"
              className="object-contain"
            />
          </div>
          <p className="num mt-4 text-center text-2xl text-gold">19 de outubro de 2026</p>
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
        <h2 id="regras" className="text-4xl">Como funcionam as temporadas?</h2>
        <p className="mt-2 max-w-prose text-lg text-muted">
          A cada temporada, uma nova disputa começa e os rankings são reiniciados. Jogue quantas vezes quiser,
          acompanhe sua evolução e tente conquistar as primeiras posições. Cada novo mapa pode melhorar sua
          classificação.
        </p>
        <dl className="mt-4 grid gap-3 md:grid-cols-3">
          <Stat label="Duração" value="1 mês" hint="Do dia 19 ao dia 18 do mês seguinte" />
          <Stat label="Confrontos" value="BO1 e BO3 livres" hint="Sem limite de confrontos ou mapas por temporada" />
          <Stat label="Pontuação" value="Top 6 mapas" hint="Os 6 melhores mapas de cada jogador contam em cada ranking" />
        </dl>
        <p className="mt-4 max-w-prose text-lg text-muted">
          Para concorrer aos títulos, é necessário disputar pelo menos 6 mapas. Ao final da temporada, os líderes dos
          rankings Elite, Superação e XP poderão conquistar os títulos de MVP, Revelação e Xinxa. Todos os resultados
          ficam registrados no histórico da liga.
        </p>
      </Card>
    </>
  );
}
