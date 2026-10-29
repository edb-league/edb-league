import Link from "next/link";
import { AchievementTabs } from "@/components/layout/SectionTabs";
import { Avatar } from "@/components/ui/Avatar";
import { EmptyState, SectionTitle } from "@/components/ui/Card";
import { Icon } from "@/components/ui/Icon";
import { PageHeader } from "@/components/ui/PageHeader";
import { api, steamAvatars } from "@/lib/api";
import { num } from "@/lib/format";
import type { Hall, PlayerRef } from "@/lib/types";

export const metadata = { title: "Hall da Fama" };

type Avatars = Record<string, string>;

/** Quem detém o recorde: foto e nome (vários nomes em caso de empate). */
function Holders({ holders, avatars, size = 36 }: { holders: PlayerRef[]; avatars: Avatars; size?: number }) {
  return (
    <ul className="flex flex-col gap-1.5">
      {holders.map((h) => (
        <li key={h.id}>
          <Link
            href={`/jogadores/${encodeURIComponent(h.id)}`}
            className="press inline-flex items-center gap-2 text-base font-bold text-fg no-underline hover:underline"
          >
            <Avatar name={h.name} src={avatars[h.id]} size={size} decorative className="border-2" />
            {h.name}
          </Link>
        </li>
      ))}
    </ul>
  );
}

function Henio({ henio, avatars }: { henio: Hall["henio"]; avatars: Avatars }) {
  return (
    <div className="card flex flex-col gap-2 border-2 border-gold-bg p-4">
      <h3 className="text-lg font-bold">Prêmio Henio · jogador com pior ADR</h3>
      <p className="text-base text-muted">Homenagem da EDB LEAGUE</p>
      {henio ? (
        <>
          <p className="num text-4xl leading-none text-gold">{num(henio.adr, 1)} ADR</p>
          <Holders holders={henio.holders} avatars={avatars} size={44} />
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

const TITLE_RANKING = { MVP: "Ranking Elite", Revelação: "Ranking Superação", Xinxa: "Ranking XP" } as const;

export default async function HallPage() {
  const [hall, avatars] = await Promise.all([api<Hall>("/hall-of-fame"), steamAvatars()]);
  const seasons = [...new Set(hall.titles.map((t) => t.season_number))].sort((a, b) => b - a);

  return (
    <>
      <PageHeader
        title="Hall da Fama"
        subtitle="Grandes jogadores constroem momentos. Lendas deixam um legado."
        art="trophy"
      />
      <AchievementTabs current="/hall-da-fama" />

      <section aria-labelledby="campeoes">
        <SectionTitle id="campeoes" title="Campeões oficiais">
          Os três títulos de cada temporada, entregues quando ela é homologada.
        </SectionTitle>
        {hall.titles.length ? (
          <div className="flex flex-col gap-6">
            {seasons.map((season) => (
              <div key={season}>
                <h3 className="mb-2 font-display text-2xl font-bold uppercase">
                  {season === 0 ? "Temporada de testes" : `Temporada ${season}`}
                </h3>
                <ul className="grid gap-3 md:grid-cols-3">
                  {hall.titles
                    .filter((t) => t.season_number === season)
                    .map((t) => (
                      <li key={t.title} className="card flex items-center gap-4 border-gold p-4">
                        {t.player ? (
                          <Avatar name={t.player.name} src={avatars[t.player.id]} size={64} decorative />
                        ) : (
                          <Avatar name="?" size={64} decorative />
                        )}
                        <div className="min-w-0">
                          <p className="flex items-center gap-1.5 text-base font-bold text-gold">
                            <Icon name="star" /> {t.title}
                            <span className="font-normal text-muted">· {TITLE_RANKING[t.title]}</span>
                          </p>
                          <p className="text-2xl leading-tight font-bold break-words">
                            {t.player ? (
                              <Link
                                href={`/jogadores/${encodeURIComponent(t.player.id)}`}
                                className="text-fg no-underline hover:underline"
                              >
                                {t.player.name}
                              </Link>
                            ) : (
                              "Não identificado"
                            )}
                          </p>
                          <p className="num text-xl text-muted">{num(t.score, t.ranking === "xp" ? 0 : 1)}</p>
                        </div>
                      </li>
                    ))}
                </ul>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState>A primeira premiação oficial será homologada após a Temporada 1.</EmptyState>
        )}
      </section>

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
                    <li key={t.player.id} className="flex items-center justify-between gap-3 px-4 py-2.5 text-base">
                      <span className="flex min-w-0 items-center gap-3">
                        <b className={`num w-5 text-xl ${i === 0 ? "text-gold" : "text-muted"}`}>{i + 1}</b>
                        <Link
                          href={`/jogadores/${encodeURIComponent(t.player.id)}`}
                          className="press flex min-w-0 items-center gap-2 font-bold text-fg no-underline hover:underline"
                        >
                          <Avatar name={t.player.name} src={avatars[t.player.id]} size={32} decorative className="border-2" />
                          <span className="truncate">{t.player.name}</span>
                        </Link>
                      </span>
                      <b className="tabular">{num(t.kills)} kills</b>
                    </li>
                  ))}
                </ol>
              </section>
            )}
            <Henio henio={hall.henio} avatars={avatars} />
          </div>

          <section aria-labelledby="recordes">
            <SectionTitle id="recordes" title="Recordes da EDB LEAGUE" />
            <ul className="grid gap-3 sm:grid-cols-2">
              {hall.records.map((r) => (
                <li key={r.title} className="card flex flex-col gap-2 p-4">
                  <h3 className="text-base font-bold text-muted">{r.title}</h3>
                  <p className="num text-4xl leading-none text-gold">{r.value}</p>
                  <Holders holders={r.holders.slice(0, 3)} avatars={avatars} />
                  {r.holders.length > 3 && <p className="text-sm text-muted">e mais {r.holders.length - 3}</p>}
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
    </>
  );
}
