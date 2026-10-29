import Image from "next/image";
import Link from "next/link";
import { SeasonBar } from "@/components/layout/SeasonBar";
import { Badge, TeamTag } from "@/components/ui/Badge";
import { Card, EmptyState, SectionTitle } from "@/components/ui/Card";
import { Fmt, MapTile } from "@/components/ui/MapTile";
import { LinkButton } from "@/components/ui/Button";
import { api, qs, steamAvatars } from "@/lib/api";
import { Avatar } from "@/components/ui/Avatar";
import { YouBadge } from "@/components/ui/Badge";
import { getMe } from "@/lib/me";
import { num, seasonQuery } from "@/lib/format";
import { seasonContext } from "@/lib/season";
import type { Home, MatchesList, MissionPlayer, Missions, Ranking, RankingRow, SeriesCard } from "@/lib/types";
import { Icon } from "@/components/ui/Icon";

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
    <section aria-labelledby="ultimo" className="card flex flex-col gap-3 bg-surface/90 p-4">
      <div className="flex items-center justify-between gap-2">
        <h2 id="ultimo" className="text-base text-muted">Último confronto</h2>
        <Badge tone="accent"><Fmt format={series.format} /></Badge>
      </div>
      <p className="sr-only">{text}</p>
      <div aria-hidden="true" className="grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-2 text-center sm:gap-3">
        <span className="flex flex-col items-center gap-1">
          <TeamTag name={series.left} />
          <span className="text-sm text-muted">{leftWins ? <><Icon name="check" /> Vencedor</> : rightWins ? <><Icon name="x" /> Derrotado</> : ""}</span>
        </span>
        <span className="num flex items-center gap-2 text-4xl leading-none sm:text-5xl">
          <span className={leftWins ? "text-win" : rightWins ? "text-loss" : ""}>{series.score_left}</span>
          <span className="text-3xl text-muted">x</span>
          <span className={rightWins ? "text-win" : leftWins ? "text-loss" : ""}>{series.score_right}</span>
        </span>
        <span className="flex flex-col items-center gap-1">
          <TeamTag name={series.right} />
          <span className="text-sm text-muted">{rightWins ? <><Icon name="check" /> Vencedor</> : leftWins ? <><Icon name="x" /> Derrotado</> : ""}</span>
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
      <Link href={`/partidas${seasonQuery(season, { confronto: series.id })}#confronto-${series.id}`} className="link-cta">
        Ver mapas do confronto <Icon name="arrow-right" />
      </Link>
    </section>
  );
}

export default async function HomePage({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const { meta, season } = await seasonContext((await searchParams).temporada);
  const [home, elite, matches, avatars] = await Promise.all([
    api<Home>(`/home${qs({ season })}`),
    api<Ranking>(`/rankings/elite${qs({ season })}`),
    api<MatchesList>(`/matches${qs({ season })}`),
    steamAvatars(),
  ]);
  const levelOf = new Map(elite.rows.map((r) => [r.player_id, r.level]));
  const me = await getMe();
  const mine = me.player;
  // "Sua posição" só busca o que falta quando há um jogador logado.
  const standing = mine
    ? await Promise.all([
        api<Ranking>(`/rankings/xp${qs({ season })}`),
        api<Ranking>(`/rankings/superacao${qs({ season })}`),
        api<Missions>(`/missions${qs({ season })}`),
      ])
    : null;
  const recent = recentSeries(matches);
  const last = recent[0] ?? null;
  const top = elite.rows.slice(0, 8);
  const eliteMax = Math.max(...top.map((r) => r.elite ?? 0), 1);

  return (
    <>
      <section
        aria-labelledby="hero"
        className="relative isolate overflow-hidden rounded-[var(--radius-card)] border border-t-4 border-line-soft border-t-gold-bg bg-surface-2"
      >
        <Image src="/art/home.webp" alt="" fill priority sizes="100vw" className="-z-20 object-cover object-right" />
        <div aria-hidden="true" className="absolute inset-0 -z-10 bg-surface-2/92 lg:bg-linear-to-r lg:from-surface-2 lg:from-45% lg:via-surface-2/88 lg:to-surface-2/60" />
        <div className="grid grid-cols-[minmax(0,1fr)] items-center gap-8 px-5 py-6 md:px-10 md:py-8 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)]">
          <div>
            <h1 id="hero" className="text-5xl leading-none md:text-6xl">Os Xinxas agora têm ranking.</h1>
            <p className="mt-4 max-w-prose text-xl text-muted">Cada frag conta. Cada evolução importa. A temporada começa aqui.</p>
            <div className="mt-5 flex flex-wrap gap-3">
              <LinkButton href={`/rankings/elite${seasonQuery(season)}`} variant="gold">Ver o ranking</LinkButton>
              <LinkButton href={`/partidas${seasonQuery(season)}`} variant="secondary">Ver partidas</LinkButton>
            </div>
          </div>
          <div className="flex flex-col gap-4">
            {last && <LastSeries series={last} season={season} />}
          </div>
        </div>
        <div className="border-t border-line-soft bg-surface/92 px-5 py-2 md:px-10">
          <SeasonBar meta={meta} season={season} path="/" variant="strip" />
        </div>
      </section>

      {mine && standing && (
        <MyStanding
          me={mine}
          avatar={avatars[mine.id]}
          season={elite.season.label}
          rows={{ elite: elite.rows, xp: standing[0].rows, superacao: standing[1].rows }}
          mission={standing[2].players.find((p) => p.player.id === mine.id) ?? null}
          week={standing[2].week?.number ?? null}
        />
      )}

      <section aria-labelledby="destaques">
        <SectionTitle id="destaques" title="Destaques da temporada">
          {`${num(home.counts.players)} jogadores ativos e ${num(home.counts.matches)} ${home.counts.matches === 1 ? "mapa registrado" : "mapas registrados"} na temporada.`}
        </SectionTitle>
        <ul className="grid gap-4 md:grid-cols-3">
          {home.highlights.map((h) => (
            <li key={h.title} className={h.title === "MVP" ? "card border-2 border-gold-bg p-5" : "card p-5"}>
              <p className="text-base text-muted">
                <b className={h.title === "MVP" ? "text-gold" : "text-fg"}>{h.title}</b> · {RANKING_NAME[h.ranking]}
              </p>
              <div className="mt-3 flex items-center gap-3">
                {h.player && (
                  <Avatar name={h.player.name} src={avatars[h.player.id]} size={56} level={levelOf.get(h.player.id) ?? null} decorative className="border-2" />
                )}
                <p className="num text-4xl leading-tight break-words">
                  {h.player ? (
                    <Link href={`/jogadores/${encodeURIComponent(h.player.id)}`} className="text-fg no-underline hover:underline">{h.player.name}</Link>
                  ) : (
                    "A definir"
                  )}
                </p>
              </div>
              <p className="mt-1 text-base text-muted">{h.detail}</p>
            </li>
          ))}
        </ul>
      </section>

      <div className="grid grid-cols-[minmax(0,1fr)] gap-6 lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
        <Card aria-labelledby="elite-titulo">
          <SectionTitle id="elite-titulo" title="Classificação Elite">
            Os líderes do índice Elite com base no desempenho dos mapas da temporada.
          </SectionTitle>
          {top.length ? (
            <ol aria-label="Oito primeiros do ranking Elite" className="divide-y divide-line-soft rounded-lg border border-line-soft bg-surface">
              {top.map((r) => (
                <li key={r.player_id} className="card-press grid grid-cols-[2rem_minmax(0,1fr)_auto] items-center gap-3 px-3 py-2.5">
                  <span className={`num text-center text-3xl leading-none ${r.rank === 1 ? "text-gold" : "text-muted"}`}>
                    <span className="sr-only">Posição </span>
                    {r.rank}
                  </span>
                  <div className="min-w-0">
                    <div className="flex min-w-0 items-center gap-2.5">
                      <Avatar name={r.name} src={avatars[r.player_id]} size={44} level={r.level} decorative className="border-2" />
                      <div className="min-w-0">
                        <Link href={`/jogadores/${encodeURIComponent(r.player_id)}`} className="block truncate text-lg leading-tight font-bold text-fg">
                          {r.name}
                          {r.player_id === mine?.id && <YouBadge className="ml-2 align-middle" />}
                        </Link>
                        <p className="text-sm text-muted">
                          K/D {num(r.kd, 2)} · ADR {num(r.adr, 1)}
                          {r.provisional && " · provisório"}
                        </p>
                      </div>
                    </div>
                    <span aria-hidden="true" className="mt-1.5 block h-1.5 overflow-hidden rounded-full bg-surface-3">
                      <span
                        className={`block h-full rounded-full ${r.rank === 1 ? "bg-gold-bg" : "bg-accent-bg/70"}`}
                        style={{ width: `${Math.max(4, ((r.elite ?? 0) / eliteMax) * 100)}%` }}
                      />
                    </span>
                  </div>
                  <span className={`num text-3xl leading-none ${r.rank === 1 ? "text-gold" : ""}`}>{num(r.elite, 1)}</span>
                </li>
              ))}
            </ol>
          ) : (
            <EmptyState>O ranking será exibido após o registro das primeiras partidas.</EmptyState>
          )}
          <p className="mt-4 text-base text-muted">
            Índice de desempenho (KPR + ADR). Classificação provisória até a homologação; são necessários 6 mapas para
            concorrer aos títulos oficiais.
          </p>
          <p className="mt-2">
            <Link href={`/rankings/elite${seasonQuery(season)}`} className="link-cta">
              Ver ranking completo <Icon name="arrow-right" />
            </Link>
          </p>
        </Card>

        <Card aria-labelledby="recentes" className="flex flex-col">
          <SectionTitle id="recentes" title="Últimas partidas">
            Os confrontos anteriores ao último, em destaque acima.
          </SectionTitle>
          {recent.length > 1 ? (
            <ul className="flex flex-col gap-3">
              {recent.slice(1, 4).map((s) => {
                const leftWins = s.winner === "left";
                const rightWins = s.winner === "right";
                return (
                  <li key={s.id} className="card-press relative rounded-xl border border-line-soft bg-surface-2 p-4 hover:bg-surface-3">
                    <p className="flex items-center justify-between gap-2 text-base text-muted">
                      <span><Fmt format={s.format} /> · {s.date_label}</span>
                    </p>
                    {s.maps.length > 0 && (
                      <ul className="mt-2 flex gap-1.5" aria-label="Mapas do confronto">
                        {s.maps.map((m) => (
                          <li key={m.id} className="min-w-0 flex-1">
                            <MapTile map={m.map} compact className="h-8 rounded-md border border-line-soft pr-2 pl-5">
                              <span className="block truncate font-display text-base leading-8 font-bold">{m.map}</span>
                            </MapTile>
                          </li>
                        ))}
                      </ul>
                    )}
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
                      href={`/partidas${seasonQuery(season, { confronto: s.id })}#confronto-${s.id}`}
                      className="link-cta mt-2 after:absolute after:inset-0 after:content-['']"
                    >
                      <span className="sr-only">
                        {s.format.toUpperCase()} de {s.date_label}: {s.left} {s.score_left} a {s.score_right} {s.right}.{" "}
                      </span>
                      Ver mapas <Icon name="arrow-right" />
                    </Link>
                  </li>
                );
              })}
            </ul>
          ) : (
            <EmptyState>Não há outros confrontos com placar nesta temporada.</EmptyState>
          )}
          <p className="mt-auto pt-3">
            <Link href={`/partidas${seasonQuery(season)}`} className="link-cta">
              Ver todas as partidas <Icon name="arrow-right" />
            </Link>
          </p>
        </Card>
      </div>

      <section aria-labelledby="atalhos">
        <h2 id="atalhos" className="sr-only">Atalhos</h2>
        <ul className="grid gap-4 md:grid-cols-3">
          {([
            { href: "/sorteador", icon: "shuffle", title: "Sorteador de times", text: "Divida os 10 presentes em PT e PL com a menor diferença de nível." },
            { href: "/regulamento", icon: "book", title: "Regulamento", text: "Temporadas, rankings, títulos, XP e medalhas em um só lugar." },
            { href: "/comparar", icon: "versus", title: "Comparar jogadores", text: "Desempenho, vitórias e confrontos lado a lado." },
          ] as const).map(({ href, icon, title, text }) => (
            <li key={href} className="card card-press group relative flex min-w-0 items-start gap-3 p-4 hover:bg-surface-2 sm:gap-4 sm:p-5">
              <span aria-hidden="true" className="inline-flex size-10 shrink-0 items-center justify-center rounded-xl bg-surface-3 text-xl text-gold sm:size-12 sm:text-2xl">
                <Icon name={icon} />
              </span>
              <div className="min-w-0 flex-1">
              <h3 className="font-display text-2xl font-bold uppercase sm:text-3xl">
                <Link href={href} className="text-fg no-underline group-hover:underline after:absolute after:inset-0 after:content-['']">
                  {title}
                </Link>
              </h3>
              <p className="mt-1 text-base text-muted">{text}</p>
              </div>
              <Icon name="arrow-right" className="mt-2 text-xl text-muted transition-transform duration-150 group-hover:translate-x-0.5 group-hover:text-fg" />
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}

const MISSION_TEXT: Record<MissionPlayer["status"], string> = {
  done: "Cumprida, +100 XP",
  unselected: "Meta batida, fora dos 6 mapas do XP",
  open: "Ainda não bateu a meta",
  none: "Sem partidas na semana",
};

/** Cartão de quem está logado: onde está em cada ranking e como vai a missão da semana. */
function MyStanding({
  me,
  avatar,
  season,
  rows,
  mission,
  week,
}: {
  me: NonNullable<Awaited<ReturnType<typeof getMe>>["player"]>;
  avatar?: string;
  season: string;
  rows: { elite: RankingRow[]; xp: RankingRow[]; superacao: RankingRow[] };
  mission: MissionPlayer | null;
  week: number | null;
}) {
  const find = (list: RankingRow[]) => list.find((r) => r.player_id === me.id) ?? null;
  const items = [
    { label: "Elite", row: find(rows.elite), value: (r: RankingRow) => num(r.elite, 1) },
    { label: "Superação", row: find(rows.superacao), value: (r: RankingRow) => num(r.superacao, 1, "%") },
    { label: "XP", row: find(rows.xp), value: (r: RankingRow) => num(r.xp) },
  ];
  return (
    <section aria-labelledby="minha-posicao" className="card border-2 border-accent p-4 md:p-6">
      <div className="flex flex-wrap items-center gap-4">
        <Avatar name={me.name} src={avatar} size={64} level={me.level} decorative className="border-2" />
        <div className="min-w-0 flex-1">
          <h2 id="minha-posicao" className="text-3xl leading-tight">
            Olá, {me.nickname}
          </h2>
          <p className="text-base text-muted">Sua posição na {season}</p>
        </div>
        <LinkButton href={`/jogadores/${encodeURIComponent(me.id)}`} variant="secondary">
          Meu perfil <Icon name="arrow-right" />
        </LinkButton>
      </div>
      <dl className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-4">
        {items.map(({ label, row, value }) => (
          <div key={label} className="rounded-xl border border-line-soft bg-surface-2 p-3">
            <dt className="text-base text-muted">{label}</dt>
            <dd className="num text-4xl leading-none">{row ? `${row.rank}º` : "–"}</dd>
            <dd className="mt-1 text-sm text-muted">
              {row ? (
                <>
                  {value(row)}
                  {row.provisional && " · provisório"}
                </>
              ) : (
                "Sem partidas ainda"
              )}
            </dd>
          </div>
        ))}
        <div className="rounded-xl border border-line-soft bg-surface-2 p-3">
          <dt className="text-base text-muted">Missão da semana{week ? ` ${week}` : ""}</dt>
          <dd className={`text-xl leading-tight font-bold ${mission?.status === "done" ? "text-win" : ""}`}>
            {mission ? MISSION_TEXT[mission.status] : "Sem dados"}
          </dd>
          {mission && mission.status === "open" && mission.best_kpr !== null && (
            <dd className="mt-1 text-sm text-muted">
              Melhor KPR da semana {num(mission.best_kpr, 2)} de {num(mission.target, 2)}
            </dd>
          )}
          {mission && mission.status !== "open" && (
            <dd className="mt-1 text-sm text-muted">
              <Link href="/missoes-xp">Ver a missão</Link>
            </dd>
          )}
        </div>
      </dl>
    </section>
  );
}
