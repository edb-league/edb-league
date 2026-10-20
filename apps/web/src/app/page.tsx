import Image from "next/image";
import Link from "next/link";
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

/** Séries com placar, da mais recente para a mais antiga, pela data do último mapa. */
function recentSeries(list: MatchesList): SeriesCard[] {
  return [...list.bo1, ...list.bo3]
    .filter((s) => s.score_left !== null && s.score_right !== null)
    .map((s) => ({ s, date: s.maps.map((m) => m.date ?? "").sort().at(-1) ?? "" }))
    .sort((a, b) => b.date.localeCompare(a.date))
    .map((x) => x.s);
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
  const recent = recentSeries(matches);
  const last = recent[0] ?? null;
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

        <Card aria-labelledby="recentes" className="flex flex-col">
          <SectionTitle id="recentes" kicker="Resultados" title="Últimas partidas">
            Os confrontos mais recentes da temporada.
          </SectionTitle>
          {recent.length ? (
            <ul className="flex flex-col gap-3">
              {recent.slice(0, 3).map((s) => {
                const leftWins = s.winner === "left";
                const rightWins = s.winner === "right";
                return (
                  <li key={s.id} className="relative rounded-xl border border-line-soft bg-surface-2 p-4 hover:bg-surface-3">
                    <p className="flex items-center justify-between gap-2 text-base text-muted">
                      <span>{s.format.toUpperCase()} · {s.date_label}</span>
                      <span>{s.maps.map((m) => m.map).join(", ")}</span>
                    </p>
                    <p className="mt-2 flex items-center justify-between gap-3">
                      <TeamTag name={s.left} />
                      <span className="num flex items-center gap-2 text-4xl leading-none">
                        <span className={leftWins ? "text-win" : rightWins ? "text-loss" : ""}>{s.score_left}</span>
                        <span className="text-xl text-muted">x</span>
                        <span className={rightWins ? "text-win" : leftWins ? "text-loss" : ""}>{s.score_right}</span>
                      </span>
                      <TeamTag name={s.right} />
                    </p>
                    <Link
                      href={`/partidas${seasonQuery(season, { confronto: s.id })}#mapas-do-confronto`}
                      className="mt-2 inline-flex min-h-11 items-center text-base font-bold after:absolute after:inset-0 after:content-['']"
                    >
                      <span className="sr-only">
                        {s.format.toUpperCase()} de {s.date_label}: {s.left} {s.score_left} a {s.score_right} {s.right}.{" "}
                      </span>
                      Ver mapas →
                    </Link>
                  </li>
                );
              })}
            </ul>
          ) : (
            <EmptyState>Nenhum confronto com placar nesta temporada.</EmptyState>
          )}
          <p className="mt-auto pt-3">
            <Link href={`/partidas${seasonQuery(season)}`} className="inline-flex min-h-11 items-center text-base font-bold">
              Ver todas as partidas →
            </Link>
          </p>
        </Card>
      </div>

      <section aria-labelledby="atalhos">
        <h2 id="atalhos" className="sr-only">Atalhos</h2>
        <ul className="grid gap-4 md:grid-cols-3">
          {[
            { href: "/sorteador", kicker: "Ferramentas", title: "Sorteador de times", text: "Divida os 10 presentes em PT e PL com a menor diferença de nível." },
            { href: "/regulamento", kicker: "Liga", title: "Regulamento", text: "Temporadas, rankings, títulos, XP e medalhas em um só lugar." },
            { href: "/comparar", kicker: "Ferramentas", title: "Comparar jogadores", text: "Desempenho, vitórias e confrontos lado a lado." },
          ].map(({ href, kicker, title, text }) => (
            <li key={href} className="card group relative p-5 hover:bg-surface-2">
              <p className="kicker">{kicker}</p>
              <h3 className="mt-1 font-display text-3xl font-bold uppercase">
                <Link href={href} className="text-fg no-underline group-hover:underline after:absolute after:inset-0 after:content-['']">
                  {title}
                </Link>
              </h3>
              <p className="mt-1 text-base text-muted">{text}</p>
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}
