import Image from "next/image";
import Link from "next/link";
import { Evolution } from "@/components/players/Evolution";
import { MedalCard } from "@/components/players/MedalCard";
import { Badge, OutcomeBadge } from "@/components/ui/Badge";
import { Card, EmptyState, SectionTitle } from "@/components/ui/Card";
import { StyleBars, type StyleItem } from "@/components/players/StyleBars";
import { FormStrip, LevelBadge } from "@/components/ui/LevelBadge";
import { LinkButton } from "@/components/ui/Button";
import { Stat, StatGrid } from "@/components/ui/Stat";
import { TableWrap, Td, Th } from "@/components/ui/Table";
import { api, apiOrNotFound, qs } from "@/lib/api";
import { dateBR, hoursLabel, num, seasonQuery, signed } from "@/lib/format";
import { seasonContext } from "@/lib/season";
import type { Hall, PlayerDetail, Ranking, RankingRow } from "@/lib/types";
import { NoData } from "@/components/ui/NoData";

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  try {
    const d = await apiOrNotFound<PlayerDetail>(`/players/${encodeURIComponent(id)}`);
    return { title: d.player.name };
  } catch {
    return { title: "Jogador" };
  }
}

function Silhouette() {
  return (
    <svg role="img" aria-label="Sem foto da Steam" viewBox="0 0 96 96" className="size-24 rounded-full border-2 border-line">
      <rect width="96" height="96" fill="var(--surface-3)" />
      <circle cx="48" cy="36" r="17" fill="var(--text-subtle)" />
      <path d="M14 96c0-21 15-34 34-34s34 13 34 34z" fill="var(--text-subtle)" />
    </svg>
  );
}

/** Posição (0 a 100) entre os jogadores da liga: 100 = melhor valor, 0 = pior. */
function standing(value: number | null | undefined, all: (number | null | undefined)[]): number | null {
  if (value === null || value === undefined) return null;
  const vals = all.filter((v): v is number => v !== null && v !== undefined);
  if (vals.length < 2) return null;
  const above = vals.filter((v) => v > value).length;
  return Math.round((100 * (vals.length - 1 - above)) / (vals.length - 1));
}

const mean = (vals: (number | null | undefined)[]): number | null => {
  const v = vals.filter((x): x is number => x !== null && x !== undefined);
  return v.length ? v.reduce((a, b) => a + b, 0) / v.length : null;
};

const winRate = (r: RankingRow) => (r.matches > 0 ? (100 * r.wins) / r.matches : null);

function Comparison({
  label,
  value,
  avg,
  decimals,
  suffix = "",
}: {
  label: string;
  value: number | null;
  avg: number | null;
  decimals: number;
  suffix?: string;
}) {
  const diff = value !== null && avg !== null ? value - avg : null;
  const tone =
    diff === null
      ? "bg-surface-3 text-muted"
      : diff > 0
        ? "bg-win-bg text-win"
        : diff < 0
          ? "bg-loss-bg text-loss"
          : "bg-surface-3 text-fg";
  const mark = diff === null ? "" : diff > 0 ? "▲" : diff < 0 ? "▼" : "●";
  return (
    <li className="card flex flex-col gap-1 p-4">
      <p className="text-base font-semibold text-muted">{label}</p>
      <p className="num text-5xl leading-none">{num(value, decimals, suffix)}</p>
      <p className="text-base text-muted">Liga: {num(avg, decimals, suffix)}</p>
      {diff !== null && (
        <span className={`mt-1 inline-flex w-fit items-center gap-1 rounded-full px-2.5 py-0.5 text-sm font-bold ${tone}`}>
          <span aria-hidden="true">{mark}</span>
          {signed(diff, decimals, suffix)}
          <span className="sr-only">
            {diff > 0 ? " acima da média da liga" : diff < 0 ? " abaixo da média da liga" : " na média da liga"}
          </span>
        </span>
      )}
    </li>
  );
}

function RatingChip({ rating }: { rating: number | null }) {
  if (rating === null) return <>–</>;
  const hi = rating >= 1.1,
    lo = rating <= 0.9;
  return (
    <span
      className={`num inline-flex min-w-18 items-center justify-end gap-1 rounded-md px-2 py-0.5 text-xl ${hi ? "bg-win-bg text-win" : lo ? "bg-loss-bg text-loss" : "bg-surface-3 text-fg"}`}
    >
      <span aria-hidden="true" className="text-sm">
        {hi ? "▲" : lo ? "▼" : "●"}
      </span>
      {num(rating, 2)}
      <span className="sr-only">{hi ? ", acima de 1,10" : lo ? ", abaixo de 0,90" : ""}</span>
    </span>
  );
}

const TABS = [
  ["resumo", "Resumo"],
  ["partidas", "Partidas"],
  ["medalhas", "Medalhas e títulos"],
] as const;

export default async function PlayerPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { id } = await params;
  const sp = await searchParams;
  const { season } = await seasonContext(sp.temporada);
  const tabRaw = Array.isArray(sp.aba) ? sp.aba[0] : sp.aba;
  const tab = TABS.find(([key]) => key === tabRaw)?.[0] ?? "resumo";
  const [d, elite, hall] = await Promise.all([
    apiOrNotFound<PlayerDetail>(`/players/${encodeURIComponent(id)}`),
    api<Ranking>(`/rankings/elite${qs({ season })}`),
    api<Hall>("/hall-of-fame"),
  ]);
  const { player, steam, summary } = d;
  const games = summary.games;
  const earned = d.medals.filter((m) => m.earned);
  const locked = d.medals.filter((m) => !m.earned);
  const next = locked
    .filter((m) => m.progress !== null)
    .sort((a, b) => (b.progress ?? 0) - (a.progress ?? 0))
    .slice(0, 4);

  const rowsAll = elite.rows.filter((r) => r.matches > 0);
  const row = elite.rows.find((r) => r.player_id === player.id) ?? null;
  const titles = hall.titles.filter((t) => t.player?.id === player.id);
  const ratings = d.matches.map((m) => m.rating).filter((r): r is number => r !== null);
  const meanRating = ratings.length ? ratings.reduce((a, b) => a + b, 0) / ratings.length : null;
  const form = d.matches.slice(0, 10).map((m) => m.result);
  const wins10 = form.filter((r) => r === "win").length;
  const losses10 = form.filter((r) => r === "loss").length;

  const styles: StyleItem[] = row
    ? [
        {
          label: "Poder de fogo",
          basis: `ADR ${num(row.adr, 1)}`,
          score: standing(
            row.adr,
            rowsAll.map((r) => r.adr),
          ),
        },
        {
          label: "Abates",
          basis: `kills por round ${num(row.kpr, 2)}`,
          score: standing(
            row.kpr,
            rowsAll.map((r) => r.kpr),
          ),
        },
        {
          label: "Sobrevivência",
          basis: `K/D ${num(row.kd, 2)}`,
          score: standing(
            row.kd,
            rowsAll.map((r) => r.kd),
          ),
        },
        {
          label: "Vitórias",
          basis: `${num(winRate(row), 0, "%")} de aproveitamento`,
          score: standing(winRate(row), rowsAll.map(winRate)),
        },
      ]
    : [];

  return (
    <>
      <p>
        <Link href="/jogadores" className="inline-flex min-h-11 items-center text-base font-bold">
          ← Todos os jogadores
        </Link>
      </p>

      <header className="card border-t-4 border-t-gold-bg p-4 md:p-6">
        <div className="flex flex-wrap items-center justify-between gap-6">
          <div className="flex flex-wrap items-center gap-5">
            {steam.avatar ? (
              <Image
                src={steam.avatar}
                alt={`Foto de ${player.name}`}
                width={96}
                height={96}
                unoptimized
                className="size-24 rounded-full border-[3px] border-gold-bg object-cover"
              />
            ) : (
              <Silhouette />
            )}
            <div className="min-w-0">
              <p className="kicker">Perfil do jogador</p>
              <h1 className="text-5xl leading-none break-words">{player.nickname}</h1>
              {player.real_name && <p className="mt-1 text-xl text-muted">{player.real_name}</p>}
              <ul className="mt-3 flex flex-wrap items-center gap-2 text-base">
                <li className="inline-flex items-center gap-2 rounded-full border border-line-soft bg-surface-2 py-1 pr-3 pl-1.5 font-semibold">
                  <LevelBadge level={player.level} />
                  Nível {player.level}
                </li>
                {player.stars > 0 && (
                  <li className="rounded-full border border-line-soft bg-surface-2 px-3 py-1 font-semibold">
                    <span aria-hidden="true" className="mr-1.5 tracking-widest text-gold">
                      {"★".repeat(player.stars)}
                    </span>
                    {player.stars} {player.stars === 1 ? "estrela" : "estrelas"}
                  </li>
                )}
                {row && (
                  <li className="rounded-full border border-gold-bg bg-surface-2 px-3 py-1 font-semibold text-gold">
                    {row.rank}º no Ranking Elite
                  </li>
                )}
                {!player.is_active && (
                  <li>
                    <Badge>Fora do elenco ativo</Badge>
                  </li>
                )}
                {steam.persona && (
                  <li className="rounded-full border border-line-soft bg-surface-2 px-3 py-1">Steam: {steam.persona}</li>
                )}
              </ul>
              <p className="mt-2 flex items-baseline gap-2">
                <b className="num text-3xl leading-none text-gold">{hoursLabel(steam.hours)}</b>
                <span className="text-sm font-bold tracking-wider text-muted">HORAS DE CS</span>
              </p>
              {steam.note && <p className="text-sm text-muted">{steam.note}</p>}
            </div>
          </div>
          <dl className="flex flex-wrap gap-3">
            <div className="card min-w-36 bg-surface-2 px-4 py-3">
              <dt className="text-base font-semibold text-muted">Rating médio</dt>
              <dd className="num text-5xl leading-none text-gold">{num(meanRating, 2)}</dd>
              <dd className="text-sm text-muted">
                {games} {games === 1 ? "partida" : "partidas"}
              </dd>
            </div>
            <div className="card min-w-36 bg-surface-2 px-4 py-3">
              <dt className="text-base font-semibold text-muted">Índice Elite</dt>
              <dd className="num text-5xl leading-none">{num(row?.elite, 1)}</dd>
              <dd className="text-sm text-muted">
                {row ? `${row.rank}º de ${rowsAll.length}` : `Sem partidas na ${elite.season.label}`}
              </dd>
            </div>
          </dl>
        </div>
      </header>

      <nav aria-label="Seções do perfil" className="flex flex-wrap items-center justify-between gap-3 border-b border-line-soft">
        <ul className="flex flex-wrap gap-1">
          {TABS.map(([key, label]) => (
            <li key={key}>
              <Link
                href={`/jogadores/${encodeURIComponent(player.id)}${seasonQuery(season, { aba: key === "resumo" ? undefined : key })}`}
                aria-current={tab === key ? "page" : undefined}
                className={`flex min-h-12 items-center border-b-[3px] px-4 text-lg font-medium no-underline hover:border-gold-bg hover:text-fg ${
                  tab === key ? "border-gold-bg text-fg" : "border-transparent text-muted"
                }`}
              >
                {label}
              </Link>
            </li>
          ))}
        </ul>
        <LinkButton href={`/comparar?a=${encodeURIComponent(player.id)}`} variant="secondary">
          Comparar com outro jogador
        </LinkButton>
      </nav>

      {tab === "resumo" && (
        <section id="resumo" aria-labelledby="resumo-titulo" className="flex flex-col gap-5">
          <h2 id="resumo-titulo" className="text-3xl">
            Resumo da {elite.season.label}
          </h2>

          {row ? (
            <ul className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-5">
              <Comparison label="K/D" value={row.kd} avg={mean(rowsAll.map((r) => r.kd))} decimals={2} />
              <Comparison label="Kills por round" value={row.kpr} avg={mean(rowsAll.map((r) => r.kpr))} decimals={2} />
              <Comparison label="ADR" value={row.adr} avg={mean(rowsAll.map((r) => r.adr))} decimals={1} />
              <Comparison label="Aproveitamento" value={winRate(row)} avg={mean(rowsAll.map(winRate))} decimals={0} suffix="%" />
              <Comparison label="Partidas" value={row.matches} avg={mean(rowsAll.map((r) => r.matches))} decimals={0} />
            </ul>
          ) : (
            <EmptyState>Sem partidas na {elite.season.label}. Os totais de todas as temporadas estão abaixo.</EmptyState>
          )}

          <div className="grid gap-5 lg:grid-cols-[3fr_2fr]">
            {row && (
              <Card aria-labelledby="estilo">
                <SectionTitle id="estilo" title="Estilo de jogo" level={3}>
                  Posição entre os {rowsAll.length} jogadores da liga na {elite.season.label}: 100 é o melhor, 0 o pior. O traço
                  branco marca o meio da liga.
                </SectionTitle>
                <StyleBars items={styles} />
                <p className="mt-4 text-sm text-muted">Calculado com ADR, kills por round, K/D e vitórias.</p>
              </Card>
            )}
            <div className="flex flex-col gap-5">
              <Card aria-labelledby="melhor" className="border-2 border-gold-bg">
                <h3 id="melhor" className="kicker mb-2">
                  Melhor partida
                </h3>
                {summary.best ? (
                  <>
                    <p className="num text-5xl leading-none">
                      {summary.best.kills} <span className="text-2xl font-medium text-muted">kills</span>
                    </p>
                    <p className="mt-2 text-lg text-muted">
                      {summary.best.map} · {dateBR(summary.best.date)}
                    </p>
                    <Link
                      href={`/partidas/mapa/${encodeURIComponent(summary.best.match_id)}`}
                      className="inline-flex min-h-11 items-center text-base font-bold"
                    >
                      Ver a partida →
                    </Link>
                  </>
                ) : (
                  <p className="text-base text-muted">Ainda não há partidas registradas.</p>
                )}
              </Card>
              <Card aria-labelledby="forma">
                <h3 id="forma" className="kicker mb-3">
                  Forma nas últimas {form.length || 10} partidas
                </h3>
                {form.length ? (
                  <>
                    <FormStrip
                      results={form}
                      label={`Últimas ${form.length} partidas, da mais recente: ${wins10} ${wins10 === 1 ? "vitória" : "vitórias"} e ${losses10} ${losses10 === 1 ? "derrota" : "derrotas"}`}
                    />
                    <p className="mt-3 text-base text-muted">
                      {wins10} V e {losses10} D. Mais recente à esquerda.
                    </p>
                  </>
                ) : (
                  <p className="text-base text-muted">Sem partidas.</p>
                )}
              </Card>
            </div>
          </div>

          <Card aria-labelledby="evolucao">
            <SectionTitle id="evolucao" title="Evolução por partida" level={3} />
            {d.matches.length ? (
              <Evolution matches={d.matches} />
            ) : (
              <EmptyState>Este jogador ainda não tem partidas registradas.</EmptyState>
            )}
          </Card>

          <section aria-labelledby="totais" className="card p-4">
            <h3 id="totais" className="mb-2 font-display text-xl font-bold uppercase">
              Totais de todas as partidas
            </h3>
            <dl className="grid grid-cols-2 gap-x-4 gap-y-3 sm:grid-cols-4 lg:grid-cols-8">
              {(
                [
                  ["Partidas", num(games)],
                  ["Vitórias", games ? num(summary.wins) : null],
                  ["Aproveitamento", summary.win_rate !== null ? num(summary.win_rate, 0, "%") : null],
                  ["Kills", games ? num(summary.kills) : null],
                  ["Mortes", games ? num(summary.deaths) : null],
                  ["Assistências", games ? num(summary.assists) : null],
                  ["K/D", num(summary.kd, 2)],
                  ["ADR", num(summary.adr, 1)],
                ] as const
              ).map(([label, value]) => (
                <div key={label}>
                  <dt className="text-sm text-muted">{label}</dt>
                  <dd className="num text-3xl leading-none">{value ?? <NoData />}</dd>
                </div>
              ))}
            </dl>
          </section>
        </section>
      )}

      {tab === "partidas" && (
        <section id="historico" aria-labelledby="historico-titulo">
          <SectionTitle id="historico-titulo" title="Histórico de partidas">
            Rating acima de 1,10 aparece com ▲ e abaixo de 0,90 com ▼.
          </SectionTitle>
          {d.matches.length ? (
            <TableWrap caption={`Histórico de partidas de ${player.name}`}>
              <thead>
                <tr>
                  <Th>Data</Th>
                  <Th>Mapa</Th>
                  <Th>Nick usado</Th>
                  <Th>Resultado</Th>
                  <Th numeric>K</Th>
                  <Th numeric>D</Th>
                  <Th numeric>A</Th>
                  <Th numeric>K/D</Th>
                  <Th numeric>ADR</Th>
                  <Th numeric>Rating</Th>
                </tr>
              </thead>
              <tbody>
                {d.matches.map((m) => (
                  <tr key={m.match_id}>
                    <Td className="whitespace-nowrap">
                      <Link href={`/partidas/mapa/${encodeURIComponent(m.match_id)}`}>{dateBR(m.date)}</Link>
                    </Td>
                    <Td className="font-semibold">{m.map}</Td>
                    <Td>{m.played_nick}</Td>
                    <Td>
                      <OutcomeBadge outcome={m.result} />
                    </Td>
                    <Td numeric className="num text-2xl">
                      {num(m.kills)}
                    </Td>
                    <Td numeric>{num(m.deaths)}</Td>
                    <Td numeric>{num(m.assists)}</Td>
                    <Td numeric>{num(m.kd, 2)}</Td>
                    <Td numeric>{num(m.adr, 1)}</Td>
                    <Td numeric>
                      <RatingChip rating={m.rating} />
                    </Td>
                  </tr>
                ))}
              </tbody>
            </TableWrap>
          ) : (
            <EmptyState>Sem partidas.</EmptyState>
          )}
          <p className="mt-3 text-sm text-muted">
            Os totais usam todas as partidas. O ADR acumulado é calculado por dano e rounds; partidas com rounds estimados podem
            afetá-lo.
          </p>
        </section>
      )}

      {tab === "medalhas" && (
        <section id="medalhas" aria-labelledby="medalhas-titulo" className="flex flex-col gap-5">
          <SectionTitle id="medalhas-titulo" title="Medalhas e títulos">
            {earned.length} de {d.medals.length} medalhas conquistadas
          </SectionTitle>
          <Card aria-labelledby="titulos">
            <h3 id="titulos" className="mb-2 font-display text-2xl font-bold uppercase">
              Títulos de temporada
            </h3>
            {titles.length ? (
              <ul className="flex flex-col gap-2 text-lg">
                {titles.map((t) => (
                  <li key={`${t.season_number}-${t.title}`} className="flex items-center justify-between gap-2">
                    <span>
                      <b className="text-gold">★ {t.title}</b> · Temporada {t.season_number}
                    </span>
                    <span className="num text-xl">{num(t.score, t.ranking === "xp" ? 0 : 1)}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-base text-muted">
                Nenhum título ainda. MVP, Revelação e Xinxa são entregues quando a temporada é homologada.
              </p>
            )}
          </Card>
          <div>
            {next.length > 0 && (
              <>
                <h3 className="mb-2 font-display text-2xl font-bold uppercase">Mais próximas de conquistar</h3>
                <ul className="mb-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                  {next.map((m) => (
                    <MedalCard key={m.id} medal={m} />
                  ))}
                </ul>
              </>
            )}
            {earned.length > 0 && (
              <>
                <h3 className="mb-2 font-display text-2xl font-bold uppercase">Conquistadas</h3>
                <ul className="mb-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                  {earned.map((m) => (
                    <MedalCard key={m.id} medal={m} />
                  ))}
                </ul>
              </>
            )}
            {locked.length > next.length && (
              <details>
                <summary className="cursor-pointer text-lg font-bold">Demais desafios ({locked.length - next.length})</summary>
                <ul className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                  {locked
                    .filter((m) => !next.includes(m))
                    .map((m) => (
                      <MedalCard key={m.id} medal={m} />
                    ))}
                </ul>
              </details>
            )}
            {locked.length === 0 && <p className="text-base text-muted">Todas as medalhas foram conquistadas.</p>}
          </div>
        </section>
      )}
    </>
  );
}
