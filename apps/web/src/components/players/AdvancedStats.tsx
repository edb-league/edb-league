import Link from "next/link";
import { Radar } from "@/components/players/Radar";
import { StyleBars } from "@/components/players/StyleBars";
import { Card, EmptyState, SectionTitle } from "@/components/ui/Card";
import { NoData } from "@/components/ui/NoData";
import { TableWrap, Td, Th } from "@/components/ui/Table";
import { num } from "@/lib/format";
import type { AdvancedStats, AdvMetric, StatUnit } from "@/lib/types";

/** Nome da métrica em inglês (como na HLTV) e, ao lado, o significado em português em letra menor. */
export function Bi({ en, pt }: { en: string; pt: string }) {
  return (
    <>
      {en} <span className="text-sm font-normal normal-case tracking-normal text-muted">{pt}</span>
    </>
  );
}

const SECTIONS: [keyof AdvancedStats["sections"], string, string][] = [
  ["firepower", "Firepower", "poder de fogo"],
  ["entrying", "Entrying", "entrada"],
  ["trading", "Trading", "trocas"],
  ["opening", "Opening", "abertura"],
  ["closing", "Closing", "fechamento"],
  ["sniping", "Sniping", "sniper"],
  ["utility", "Utility", "utilitários"],
];

/** Sub-abas das estatísticas, na ordem da página de jogador da HLTV. */
export const STAT_VIEWS = [
  ["overview", "Overview", "visão geral"],
  ["weapons", "Weapons", "armas"],
  ["clutches", "Clutches", "clutches"],
  ["multikills", "Multi-kills", "multi-kills"],
  ["maps", "Maps", "mapas"],
  ["teammates", "Teammates", "companheiros"],
  ["opponents", "Opponents", "adversários"],
] as const;
export type StatView = (typeof STAT_VIEWS)[number][0];

const SIDES = [
  ["", "All", "ambos"],
  ["ct", "CT", "defesa"],
  ["t", "T", "ataque"],
] as const;

export function stat(value: number | null, unit: StatUnit, decimals: number): string {
  if (value === null) return "–";
  if (unit === "pct") return num(value, decimals, "%");
  if (unit === "s") {
    if (value >= 60) {
      const minutes = Math.floor(value / 60);
      const seconds = Math.round(value - minutes * 60);
      return `${minutes} min ${String(seconds).padStart(2, "0")} s`;
    }
    return num(value, decimals, " s");
  }
  return num(value, decimals);
}

function MetricsTable({
  title,
  meaning,
  metrics,
  side,
}: {
  title: string;
  meaning: string;
  metrics: AdvMetric[];
  side: "all" | "t" | "ct";
}) {
  const split = side === "all" && metrics.some((m) => m.t !== null || m.ct !== null);
  return (
    <Card aria-label={`${title} ${meaning}`}>
      <h3 className="mb-2 font-display text-2xl font-bold uppercase">
        <Bi en={title} pt={meaning} />
      </h3>
      <TableWrap caption={`${title} (${meaning}): estatísticas do jogador`}>
        <thead>
          <tr>
            <Th>
              Stat <span className="font-normal">estatística</span>
            </Th>
            <Th numeric>{side === "all" ? "All" : side === "t" ? "T" : "CT"}</Th>
            {split && <Th numeric>T</Th>}
            {split && <Th numeric>CT</Th>}
          </tr>
        </thead>
        <tbody>
          {metrics.map((m) => (
            <tr key={m.key}>
              <Td className="font-semibold" role="rowheader">
                <Bi en={m.label} pt={m.meaning} />
                {m.adapted && (
                  <span className="ml-2 rounded border border-line-soft px-1.5 py-0.5 text-xs font-normal text-muted">
                    adaptado
                  </span>
                )}
                {m.hint && <span className="block text-sm font-normal text-muted">{m.hint}</span>}
              </Td>
              <Td numeric className="num text-xl">
                {stat(m.value, m.unit, m.decimals)}
              </Td>
              {split && <Td numeric>{stat(m.t, m.unit, m.decimals)}</Td>}
              {split && <Td numeric>{stat(m.ct, m.unit, m.decimals)}</Td>}
            </tr>
          ))}
        </tbody>
      </TableWrap>
    </Card>
  );
}

function CompanyTable({ title, meaning, rows, href }: { title: string; meaning: string; rows: AdvancedStats["teammates"]; href: (id: string) => string }) {
  return (
    <Card aria-label={`${title} ${meaning}`}>
      <h3 className="mb-2 font-display text-2xl font-bold uppercase">
        <Bi en={title} pt={meaning} />
      </h3>
      {rows.length ? (
        <TableWrap caption={`${title} (${meaning}): partidas em comum e rating médio`}>
          <thead>
            <tr>
              <Th>Jogador</Th>
              <Th numeric>Partidas</Th>
              <Th numeric>Rating</Th>
              <Th numeric>Vitórias</Th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.player.id}>
                <Td>
                  <Link href={href(r.player.id)}>{r.player.name}</Link>
                </Td>
                <Td numeric>{num(r.games)}</Td>
                <Td numeric className="num text-xl">
                  {num(r.rating, 2)}
                </Td>
                <Td numeric>{num(r.win_rate, 0, "%")}</Td>
              </tr>
            ))}
          </tbody>
        </TableWrap>
      ) : (
        <p className="text-base text-muted">Sem partidas em comum com resultado conhecido.</p>
      )}
    </Card>
  );
}

function FilterGroup({
  label,
  meaning,
  options,
}: {
  label: string;
  meaning: string;
  options: { key: string; text: string; on: boolean; href: string }[];
}) {
  const id = `filtro-${label.toLowerCase()}`;
  return (
    <div role="group" aria-labelledby={id} className="flex flex-col gap-1.5">
      <p id={id} className="kicker">
        {label} <span className="font-normal normal-case tracking-normal">{meaning}</span>
      </p>
      <ul className="flex flex-wrap gap-1.5">
        {options.map((o) => (
          <li key={o.key}>
            <Link
              href={o.href}
              scroll={false}
              aria-current={o.on ? "true" : undefined}
              className={`press lift inline-flex min-h-11 items-center rounded-lg border px-4 font-bold no-underline ${
                o.on ? "border-accent bg-accent text-on-accent" : "border-line bg-surface text-fg hover:border-accent"
              }`}
            >
              {o.text}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

/**
 * Estatísticas calculadas a partir das demos, no formato da página de jogador da HLTV.
 * Sub-abas e filtros são links: o estado fica na URL e a página funciona sem JavaScript.
 */
export function AdvancedStatsView({
  data,
  playerName,
  buildHref,
  view,
}: {
  data: AdvancedStats | null;
  playerName: string;
  /** Monta o endereço do perfil trocando só os parâmetros informados (vazio remove o filtro). */
  buildHref: (patch: Record<string, string | undefined>) => string;
  view: StatView;
}) {
  if (data === null) {
    return (
      <EmptyState>
        Nenhuma partida de {playerName} tem demo analisada ainda. Estas estatísticas dependem do arquivo .dem da partida, e
        aparecem assim que uma demo for importada.
      </EmptyState>
    );
  }
  const { coverage, filters } = data;
  const applied = filters.applied;
  const side = data.side;
  const filtered = Boolean(applied.side || applied.map || applied.format || applied.season !== null);
  const scores = data.scores.map((s) => ({ label: s.label, basis: s.meaning, score: s.value, meaning: true }));
  const hasScores = scores.some((s) => s.score !== null);
  const companyHref = (id: string) => `/jogadores/${encodeURIComponent(id)}?aba=estatisticas`;

  const filterGroups = [
    {
      label: "Side",
      meaning: "lado",
      options: SIDES.map(([key, text, pt]) => ({
        key: key || "all",
        text: key ? text : `${text} (${pt})`,
        on: (applied.side ?? "") === key,
        href: buildHref({ lado: key || undefined }),
      })),
    },
    {
      label: "Map",
      meaning: "mapa",
      options: [
        { key: "all", text: "Todos", on: !applied.map, href: buildHref({ mapa: undefined }) },
        ...filters.options.maps.map((m) => ({ key: m, text: m, on: applied.map === m, href: buildHref({ mapa: m }) })),
      ],
    },
    {
      label: "Format",
      meaning: "formato",
      options: [
        { key: "all", text: "Todos", on: !applied.format, href: buildHref({ formato: undefined }) },
        ...filters.options.formats.map((f) => ({
          key: f,
          text: f.toUpperCase(),
          on: applied.format === f,
          href: buildHref({ formato: f }),
        })),
      ],
    },
    {
      label: "Season",
      meaning: "temporada",
      options: [
        { key: "all", text: "Todas", on: applied.season === null, href: buildHref({ periodo: undefined }) },
        ...filters.options.seasons.map((n) => ({
          key: String(n),
          text: `Temporada ${n}`,
          on: applied.season === n,
          href: buildHref({ periodo: String(n) }),
        })),
      ],
    },
  ];

  return (
    <div className="flex flex-col gap-5">
      <SectionTitle id="estatisticas-titulo" title="Detailed stats">
        <span className="text-muted">estatísticas detalhadas</span>
        {" · "}
        {coverage.maps_with_demo} de {coverage.maps_total} {coverage.maps_total === 1 ? "partida tem" : "partidas têm"} demo
        analisada, somando {num(data.rounds)} rounds. As demais ficam fora destes números.
      </SectionTitle>

      <nav aria-label="Tipos de estatística">
        <ul className="flex flex-wrap gap-2">
          {STAT_VIEWS.map(([key, en, pt]) => (
            <li key={key}>
              <Link
                href={buildHref({ vista: key === "overview" ? undefined : key })}
                scroll={false}
                aria-current={view === key ? "page" : undefined}
                className={`press lift inline-flex min-h-11 items-center rounded-full border px-4 font-bold no-underline ${
                  view === key ? "border-gold-bg bg-gold-bg text-on-gold" : "border-line bg-surface text-fg hover:border-gold-bg"
                }`}
              >
                {en} <span className="ml-1.5 text-sm font-normal">{pt}</span>
              </Link>
            </li>
          ))}
        </ul>
      </nav>

      <section aria-label="Filtros" className="card flex flex-wrap gap-x-9 gap-y-4 p-4">
        {filterGroups.map((g) => (
          <FilterGroup key={g.label} {...g} />
        ))}
        {filtered && (
          <p className="flex items-end">
            <Link href={buildHref({ lado: undefined, mapa: undefined, formato: undefined, periodo: undefined })} scroll={false} className="inline-flex min-h-11 items-center font-bold">
              Limpar filtros
            </Link>
          </p>
        )}
      </section>

      {data.rounds === 0 ? (
        <EmptyState>
          Nenhuma partida de {playerName} com demo combina com estes filtros. Troque o lado, o mapa, o formato ou a temporada.
        </EmptyState>
      ) : (
        <>
          {side !== "all" && (
            <p className="text-base text-muted">
              Lado {side === "t" ? "T" : "CT"}: valem só os rounds jogados nele. O que a demo não separa por lado (armas, clutches e
              algumas métricas) aparece com traço ou com o total, conforme indicado.
            </p>
          )}

          {view === "overview" && (
            <>
              <div className="grid gap-5 lg:grid-cols-[2fr_3fr] [&>*]:min-w-0">
                <Card aria-labelledby="rating-titulo" className="border-2 border-gold-bg">
                  <h3 id="rating-titulo" className="kicker mb-2">
                    Rating
                  </h3>
                  <dl className="grid grid-cols-2 gap-4">
                    <div>
                      <dt className="text-base font-bold">
                        Rating 2.0 <span className="text-sm font-normal text-muted">estimado</span>
                      </dt>
                      <dd className="num text-7xl leading-none text-gold">{num(data.rating.rating2, 2)}</dd>
                      <dd className="text-sm text-muted">
                        T {num(data.rating.rating2_t, 2)} · CT {num(data.rating.rating2_ct, 2)}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-base font-semibold text-muted">
                        Rating 1.0 <span className="text-sm font-normal">fórmula exata</span>
                      </dt>
                      <dd className="num text-5xl leading-none">{num(data.rating.rating1, 2)}</dd>
                      <dd className="text-sm text-muted">
                        T {num(data.rating.rating1_t, 2)} · CT {num(data.rating.rating1_ct, 2)}
                      </dd>
                    </div>
                  </dl>
                  <p className="mt-3 text-sm text-muted">
                    O Rating 1.0 usa a fórmula pública da HLTV. O 2.0 é uma estimativa com a fórmula pública de 2017 e fica perto
                    do rating do SCOPE. O Rating 3.0 e o Round Swing da HLTV não são públicos e não são calculados.
                  </p>
                  {hasScores && (
                    <div className="mt-4 border-t border-line-soft pt-4">
                      <p className="mb-1 text-base font-bold">
                        Perfil de jogo <span className="text-sm font-normal text-muted">o anel tracejado é o meio da liga</span>
                      </p>
                      <Radar items={scores} />
                    </div>
                  )}
                </Card>
                <Card aria-labelledby="notas-titulo">
                  <h3 id="notas-titulo" className="kicker mb-3">
                    Ratings 0-100 <span className="font-normal normal-case tracking-normal">notas de 0 a 100</span>
                  </h3>
                  {hasScores ? (
                    <StyleBars items={scores} />
                  ) : (
                    <p className="text-base text-muted">
                      As notas comparam o jogador com os outros da liga. Elas aparecem quando pelo menos 3 jogadores têm partidas
                      com demo{filtered ? " dentro destes filtros" : ""}.
                    </p>
                  )}
                </Card>
              </div>

              <section aria-labelledby="cartoes-titulo">
                <h3 id="cartoes-titulo" className="sr-only">
                  Visão geral
                </h3>
                <ul className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                  {data.cards.map((c) => (
                    <li key={c.key} className="card p-3">
                      <p className="text-base font-semibold text-muted">{c.label}</p>
                      <p className="num text-4xl leading-none">{stat(c.value, c.unit, c.decimals)}</p>
                      <p className="mt-1 text-sm text-muted">{c.meaning}</p>
                    </li>
                  ))}
                </ul>
              </section>

              {/* Colunas (e não grade): as tabelas têm alturas diferentes e assim não sobram buracos. */}
              <div className="gap-5 lg:columns-2 [&>*]:mb-5 [&>*]:break-inside-avoid">
                {SECTIONS.map(([key, title, meaning]) => (
                  <MetricsTable key={key} title={title} meaning={meaning} metrics={data.sections[key]} side={side} />
                ))}
              </div>
              <p className="text-sm text-muted">
                Itens marcados como adaptado seguem uma definição da liga, porque a HLTV não publica a fórmula. Totais da demo:{" "}
                {num(data.totals.kills)} kills, {num(data.totals.deaths)} mortes, {num(data.totals.assists)} assistências,{" "}
                {num(data.totals.plants)} plants e {num(data.totals.defuses)} defuses.
              </p>
            </>
          )}

          {view === "multikills" && (
            <Card aria-label="Multi-kills">
              <h3 className="mb-2 font-display text-2xl font-bold uppercase">
                <Bi en="Multi-kills" pt="rounds por quantidade de kills" />
              </h3>
              <TableWrap caption="Rounds por quantidade de kills">
                <thead>
                  <tr>
                    <Th>Kills no round</Th>
                    <Th numeric>Rounds</Th>
                    <Th numeric>% dos rounds</Th>
                    {side === "all" && <Th numeric>T</Th>}
                    {side === "all" && <Th numeric>CT</Th>}
                  </tr>
                </thead>
                <tbody>
                  {data.multikills.map((m) => (
                    <tr key={m.kills}>
                      <Td role="rowheader" className="font-semibold">
                        {m.kills} {m.kills === 1 ? "kill" : "kills"}
                      </Td>
                      <Td numeric className="num text-xl">
                        {num(m.rounds)}
                      </Td>
                      <Td numeric>{num(m.pct, 1, "%")}</Td>
                      {side === "all" && <Td numeric>{num(m.t)}</Td>}
                      {side === "all" && <Td numeric>{num(m.ct)}</Td>}
                    </tr>
                  ))}
                </tbody>
              </TableWrap>
            </Card>
          )}

          {view === "clutches" && (
            <Card aria-label="Clutches">
              <h3 className="mb-2 font-display text-2xl font-bold uppercase">
                <Bi en="Clutches" pt="um jogador contra vários" />
              </h3>
              {side !== "all" && <p className="mb-2 text-sm text-muted">A demo não separa clutches por lado: a tabela mostra o total.</p>}
              <TableWrap caption="Situações de um jogador contra vários">
                <thead>
                  <tr>
                    <Th>Situação</Th>
                    <Th numeric>Tentativas</Th>
                    <Th numeric>Vencidos</Th>
                  </tr>
                </thead>
                <tbody>
                  {data.clutches.map((c) => (
                    <tr key={c.label}>
                      <Td role="rowheader" className="font-semibold">
                        {c.label}
                      </Td>
                      <Td numeric>{num(c.tries)}</Td>
                      <Td numeric className="num text-xl">
                        {num(c.won)}
                      </Td>
                    </tr>
                  ))}
                </tbody>
              </TableWrap>
            </Card>
          )}

          {view === "weapons" && (
            <Card aria-label="Weapons armas">
              <h3 className="mb-2 font-display text-2xl font-bold uppercase">
                <Bi en="Weapons" pt="armas" />
              </h3>
              {side !== "all" && <p className="mb-2 text-sm text-muted">A demo não separa armas por lado: a tabela mostra o total.</p>}
              <TableWrap caption="Kills por tipo de arma">
                <thead>
                  <tr>
                    <Th>Tipo</Th>
                    <Th numeric>Kills</Th>
                    <Th numeric>% das kills</Th>
                  </tr>
                </thead>
                <tbody>
                  {data.weapon_classes.map((w) => (
                    <tr key={w.label}>
                      <Td role="rowheader" className="font-semibold">
                        {w.label}
                      </Td>
                      <Td numeric className="num text-xl">
                        {num(w.kills)}
                      </Td>
                      <Td numeric>{num(w.pct, 1, "%")}</Td>
                    </tr>
                  ))}
                </tbody>
              </TableWrap>
              <h4 className="mt-4 mb-2 text-lg font-bold">Mais usadas</h4>
              <ul className="flex flex-col gap-2">
                {data.weapons.map((w) => (
                  <li key={w.weapon}>
                    <div className="flex items-baseline justify-between gap-3 text-base">
                      <span className="font-semibold">{w.weapon}</span>
                      <span className="tabular">
                        {num(w.kills)} {w.kills === 1 ? "kill" : "kills"} · {num(w.pct, 1, "%")}
                      </span>
                    </div>
                    <div aria-hidden="true" className="mt-1 h-2 rounded-full bg-surface-3">
                      <div className="h-full rounded-full bg-gold-bg" style={{ width: `${Math.min(100, w.pct ?? 0)}%` }} />
                    </div>
                  </li>
                ))}
              </ul>
              <h4 className="mt-4 mb-2 text-lg font-bold">Kills especiais</h4>
              <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                {data.special_kills.map((k) => (
                  <div key={k.label}>
                    <dt className="text-sm text-muted">{k.label}</dt>
                    <dd className="num text-2xl leading-none">{num(k.kills)}</dd>
                  </div>
                ))}
              </dl>
            </Card>
          )}

          {view === "maps" && (
            <Card aria-label="Maps mapas">
              <h3 className="mb-2 font-display text-2xl font-bold uppercase">
                <Bi en="Maps" pt="desempenho por mapa" />
              </h3>
              {data.maps.length ? (
                <TableWrap caption="Desempenho por mapa, com as partidas do jogador dentro dos filtros">
                  <thead>
                    <tr>
                      <Th>Mapa</Th>
                      <Th numeric>Partidas</Th>
                      <Th numeric>Vitórias</Th>
                      <Th numeric>KPR</Th>
                      <Th numeric>ADR</Th>
                      <Th numeric>Rating</Th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.maps.map((m) => (
                      <tr key={m.map}>
                        <Td role="rowheader" className="font-semibold">
                          {m.map}
                        </Td>
                        <Td numeric>{num(m.games)}</Td>
                        <Td numeric>{num(m.win_rate, 0, "%")}</Td>
                        <Td numeric>{num(m.kpr, 2)}</Td>
                        <Td numeric>{num(m.adr, 1)}</Td>
                        <Td numeric className="num text-xl">
                          {m.rating === null ? <NoData /> : num(m.rating, 2)}
                        </Td>
                      </tr>
                    ))}
                  </tbody>
                </TableWrap>
              ) : (
                <p className="text-base text-muted">Sem partidas.</p>
              )}
            </Card>
          )}

          {view === "teammates" && <CompanyTable title="Teammates" meaning="companheiros" rows={data.teammates} href={companyHref} />}
          {view === "opponents" && <CompanyTable title="Opponents" meaning="adversários" rows={data.opponents} href={companyHref} />}

          {view === "overview" && (
            <Card aria-label="Similar players jogadores parecidos">
              <h3 className="mb-2 font-display text-2xl font-bold uppercase">
                <Bi en="Similar players" pt="jogadores parecidos" />
              </h3>
              {data.similar.length ? (
                <ul className="flex flex-col gap-2 text-lg">
                  {data.similar.map((s) => (
                    <li key={s.player.id} className="flex items-center justify-between gap-3">
                      <Link href={companyHref(s.player.id)} className="font-semibold">
                        {s.player.name}
                      </Link>
                      <span className="num text-xl">{num(s.similarity, 0, "%")}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-base text-muted">A comparação aparece quando há jogadores suficientes com demo.</p>
              )}
              <p className="mt-3 text-sm text-muted">Calculado pela distância entre as sete notas de 0 a 100.</p>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
