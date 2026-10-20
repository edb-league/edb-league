import Link from "next/link";
import { StyleBars } from "@/components/players/StyleBars";
import { Card, EmptyState, SectionTitle } from "@/components/ui/Card";
import { NoData } from "@/components/ui/NoData";
import { TableWrap, Td, Th } from "@/components/ui/Table";
import { num } from "@/lib/format";
import type { AdvancedStats, AdvMetric, StatUnit } from "@/lib/types";

const SECTION_TITLES: [keyof AdvancedStats["sections"], string][] = [
  ["firepower", "Poder de fogo"],
  ["entrying", "Entrada"],
  ["trading", "Trocas"],
  ["opening", "Abertura"],
  ["closing", "Fechamento"],
  ["sniping", "Sniper"],
  ["utility", "Utilitários"],
];

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

function MetricsTable({ title, metrics }: { title: string; metrics: AdvMetric[] }) {
  const sides = metrics.some((m) => m.t !== null || m.ct !== null);
  return (
    <Card aria-label={title}>
      <h3 className="mb-2 font-display text-2xl font-bold uppercase">{title}</h3>
      <TableWrap caption={`${title}: estatísticas do jogador`}>
        <thead>
          <tr>
            <Th>Estatística</Th>
            <Th numeric>Geral</Th>
            {sides && <Th numeric>T</Th>}
            {sides && <Th numeric>CT</Th>}
          </tr>
        </thead>
        <tbody>
          {metrics.map((m) => (
            <tr key={m.key}>
              <Td className="font-semibold" role="rowheader">
                {m.label}
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
              {sides && <Td numeric>{stat(m.t, m.unit, m.decimals)}</Td>}
              {sides && <Td numeric>{stat(m.ct, m.unit, m.decimals)}</Td>}
            </tr>
          ))}
        </tbody>
      </TableWrap>
    </Card>
  );
}

function CompanyTable({ title, rows }: { title: string; rows: AdvancedStats["teammates"] }) {
  return (
    <Card aria-label={title}>
      <h3 className="mb-2 font-display text-2xl font-bold uppercase">{title}</h3>
      {rows.length ? (
        <TableWrap caption={`${title}: partidas em comum e rating médio`}>
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
                  <Link href={`/jogadores/${encodeURIComponent(r.player.id)}?aba=estatisticas`}>{r.player.name}</Link>
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

/** Estatísticas calculadas a partir das demos, no formato da página de jogador da HLTV. */
export function AdvancedStatsView({ data, playerName }: { data: AdvancedStats | null; playerName: string }) {
  if (data === null) {
    return (
      <EmptyState>
        Nenhuma partida de {playerName} tem demo analisada ainda. Estas estatísticas dependem do arquivo .dem da partida, e
        aparecem assim que uma demo for importada.
      </EmptyState>
    );
  }
  const { coverage } = data;
  const scores = data.scores.map((s) => ({ label: s.label, basis: "posição na liga", score: s.value }));
  const hasScores = scores.some((s) => s.score !== null);
  return (
    <div className="flex flex-col gap-5">
      <SectionTitle id="estatisticas-titulo" title="Estatísticas detalhadas">
        {coverage.maps_with_demo} de {coverage.maps_total} {coverage.maps_total === 1 ? "partida tem" : "partidas têm"} demo
        analisada, somando {num(data.rounds)} rounds. As demais ficam fora destes números.
      </SectionTitle>

      <div className="grid gap-5 lg:grid-cols-[2fr_3fr] [&>*]:min-w-0">
        <Card aria-labelledby="rating-titulo" className="border-2 border-gold-bg">
          <h3 id="rating-titulo" className="kicker mb-2">
            Rating
          </h3>
          <dl className="grid grid-cols-2 gap-4">
            <div>
              <dt className="text-base font-semibold text-muted">Rating 1.0</dt>
              <dd className="num text-6xl leading-none text-gold">{num(data.rating.rating1, 2)}</dd>
              <dd className="text-sm text-muted">
                T {num(data.rating.rating1_t, 2)} · CT {num(data.rating.rating1_ct, 2)}
              </dd>
            </div>
            <div>
              <dt className="text-base font-semibold text-muted">Rating 2.0 (estimado)</dt>
              <dd className="num text-6xl leading-none">{num(data.rating.rating2, 2)}</dd>
              <dd className="text-sm text-muted">
                T {num(data.rating.rating2_t, 2)} · CT {num(data.rating.rating2_ct, 2)}
              </dd>
            </div>
          </dl>
          <p className="mt-3 text-sm text-muted">
            O Rating 1.0 usa a fórmula pública da HLTV. O 2.0 é uma estimativa com a fórmula pública de 2017 e fica perto do
            rating do SCOPE. O Rating 3.0 e o Round Swing da HLTV não são públicos e não são calculados.
          </p>
        </Card>
        <Card aria-labelledby="notas-titulo">
          <h3 id="notas-titulo" className="kicker mb-3">
            Notas de 0 a 100
          </h3>
          {hasScores ? (
            <StyleBars items={scores} />
          ) : (
            <p className="text-base text-muted">
              As notas comparam o jogador com os outros da liga. Elas aparecem quando pelo menos 3 jogadores têm partidas com
              demo.
            </p>
          )}
        </Card>
      </div>

      <section aria-labelledby="cartoes-titulo">
        <h3 id="cartoes-titulo" className="sr-only">
          Visão geral
        </h3>
        <ul className="grid grid-cols-2 gap-3 sm:grid-cols-4 xl:grid-cols-8">
          {data.cards.map((c) => (
            <li key={c.key} className="card p-3">
              <p className="text-sm font-semibold text-muted">{c.label}</p>
              <p className="num text-3xl leading-none">{stat(c.value, c.unit, c.decimals)}</p>
            </li>
          ))}
        </ul>
      </section>

      <div className="grid gap-5 lg:grid-cols-2 [&>*]:min-w-0">
        {SECTION_TITLES.map(([key, title]) => (
          <MetricsTable key={key} title={title} metrics={data.sections[key]} />
        ))}

        <Card aria-label="Multi-kills">
          <h3 className="mb-2 font-display text-2xl font-bold uppercase">Multi-kills</h3>
          <TableWrap caption="Rounds por quantidade de kills">
            <thead>
              <tr>
                <Th>Kills no round</Th>
                <Th numeric>Rounds</Th>
                <Th numeric>% dos rounds</Th>
                <Th numeric>T</Th>
                <Th numeric>CT</Th>
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
                  <Td numeric>{num(m.t)}</Td>
                  <Td numeric>{num(m.ct)}</Td>
                </tr>
              ))}
            </tbody>
          </TableWrap>
        </Card>

        <Card aria-label="Clutches">
          <h3 className="mb-2 font-display text-2xl font-bold uppercase">Clutches</h3>
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

        <Card aria-label="Armas">
          <h3 className="mb-2 font-display text-2xl font-bold uppercase">Armas</h3>
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

        <Card aria-label="Mapas">
          <h3 className="mb-2 font-display text-2xl font-bold uppercase">Por mapa</h3>
          {data.maps.length ? (
            <TableWrap caption="Desempenho por mapa, com todas as partidas do jogador">
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

        <CompanyTable title="Companheiros" rows={data.teammates} />
        <CompanyTable title="Adversários" rows={data.opponents} />

        <Card aria-label="Jogadores parecidos">
          <h3 className="mb-2 font-display text-2xl font-bold uppercase">Jogadores parecidos</h3>
          {data.similar.length ? (
            <ul className="flex flex-col gap-2 text-lg">
              {data.similar.map((s) => (
                <li key={s.player.id} className="flex items-center justify-between gap-3">
                  <Link href={`/jogadores/${encodeURIComponent(s.player.id)}?aba=estatisticas`} className="font-semibold">
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
      </div>

      <p className="text-sm text-muted">
        Itens marcados como adaptado seguem uma definição da liga, porque a HLTV não publica a fórmula. Totais da demo:{" "}
        {num(data.totals.kills)} kills, {num(data.totals.deaths)} mortes, {num(data.totals.assists)} assistências,{" "}
        {num(data.totals.plants)} plants e {num(data.totals.defuses)} defuses.
      </p>
    </div>
  );
}
