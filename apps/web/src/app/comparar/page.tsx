import clsx from "clsx";
import Link from "next/link";
import { Notice } from "@/components/ui/Notice";
import { PairBars } from "@/components/ui/Charts";
import { Avatar } from "@/components/ui/Avatar";
import { Button } from "@/components/ui/Button";
import { Card, EmptyState, SectionTitle } from "@/components/ui/Card";
import { SelectField } from "@/components/ui/Field";
import { Icon, StarRow } from "@/components/ui/Icon";
import { PageHeader } from "@/components/ui/PageHeader";
import { TableWrap, Td, Th } from "@/components/ui/Table";
import { Stat } from "@/components/ui/Stat";
import { api, qs, steamAvatars } from "@/lib/api";
import { getMe } from "@/lib/me";
import { dateBR, first, num } from "@/lib/format";
import type { Compare, CompareMetric, PlayerListItem } from "@/lib/types";

export const metadata = { title: "Comparar jogadores" };

export default async function ComparePage({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const sp = await searchParams;
  const [players, avatars, me] = await Promise.all([api<PlayerListItem[]>("/players"), steamAvatars(), getMe()]);
  const sorted = [...players].sort((a, b) => a.name.localeCompare(b.name, "pt-BR"));

  const ids = new Set(sorted.map((p) => p.id));
  const askedA = first(sp.a);
  const askedB = first(sp.b);
  const mine = me.player && ids.has(me.player.id) ? me.player.id : undefined;
  const a = askedA && ids.has(askedA) ? askedA : (mine ?? sorted[0]?.id);
  const b = askedB && ids.has(askedB) ? askedB : sorted.find((p) => p.id !== a)?.id;
  const same = a !== undefined && a === b;
  const comparison = a && b && !same ? await api<Compare>(`/compare${qs({ a, b })}`) : null;

  return (
    <>
      <PageHeader
        title="Comparar jogadores"
        subtitle="Análise lado a lado: desempenho, vitórias e confrontos da liga."
        art="duel"
      />

      {sorted.length < 2 ? (
        <EmptyState>É necessário ter pelo menos dois jogadores ativos para comparar resultados.</EmptyState>
      ) : (
        <>
          {/* Formulário GET: funciona sem JavaScript e mantém o link compartilhável. */}
          <Card>
            <form method="get" action="/comparar" className="grid gap-4 md:grid-cols-[1fr_1fr_auto] md:items-end">
              <SelectField id="a" name="a" label="Jogador 1" defaultValue={a}>
                {sorted.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </SelectField>
              <SelectField id="b" name="b" label="Jogador 2" defaultValue={b}>
                {sorted.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </SelectField>
              <Button type="submit">Comparar</Button>
            </form>
          </Card>

          {same && <Notice tone="warning">Escolha dois jogadores diferentes para comparar os resultados.</Notice>}

          {comparison && <Result c={comparison} avatars={avatars} />}
        </>
      )}
    </>
  );
}

function Contender({ player, avatars, side, wins }: { player: PlayerListItem; avatars: Record<string, string>; side: "left" | "right"; wins: boolean }) {
  return (
    <div className={clsx("flex min-w-0 flex-col items-center gap-2 text-center", side === "left" ? "md:items-end md:text-right" : "md:items-start md:text-left")}>
      <Avatar name={player.name} src={avatars[player.id]} size={88} level={player.level} className={wins ? "" : "border-line-soft"} decorative />
      <div className="min-w-0">
        <h3 className="text-3xl leading-tight font-bold break-words">
          <Link href={`/jogadores/${encodeURIComponent(player.id)}`} className="text-fg no-underline hover:underline">
            {player.name}
          </Link>
        </h3>
        <p className="text-base text-muted">
          Nível {player.level}
          {player.stars > 0 && (
            <>
              {" · "}
              <span role="img" aria-label={`${player.stars} ${player.stars === 1 ? "estrela" : "estrelas"}`} className="text-gold">
                <StarRow count={player.stars} />
              </span>
            </>
          )}
        </p>
      </div>
    </div>
  );
}

/** Uma métrica em barras espelhadas: cada lado cresce a partir do centro, o melhor em ouro. */
function MetricRow({ m, n1, n2 }: { m: CompareMetric; n1: string; n2: string }) {
  const max = Math.max(m.first ?? 0, m.second ?? 0, 0.0001);
  const side = (value: number | null, who: "first" | "second", name: string) => {
    const best = m.better === who;
    const width = value === null ? 0 : Math.max(4, (value / max) * 100);
    const bar = (
      <span aria-hidden="true" className="h-3 min-w-0 flex-1 overflow-hidden rounded-full bg-surface-3">
        <span
          className={clsx("block h-full rounded-full", best ? "bg-gold-bg" : "bg-accent-bg/60", who === "first" && "ml-auto")}
          style={{ width: `${width}%` }}
        />
      </span>
    );
    const text = (
      <span className={clsx("tabular w-20 shrink-0 text-xl font-bold", who === "first" ? "text-right" : "text-left", best && "text-gold")}>
        {best && <Icon name="star" className="mr-1 text-base" />}
        <span className="sr-only">{best ? `Melhor, ${name}: ` : `${name}: `}</span>
        {num(value, m.decimals, m.suffix)}
      </span>
    );
    return (
      <div className="flex min-w-0 items-center gap-2">
        {who === "first" ? (
          <>
            {text}
            {bar}
          </>
        ) : (
          <>
            {bar}
            {text}
          </>
        )}
      </div>
    );
  };
  return (
    <li className="py-3">
      <p className="mb-1 text-center text-base font-bold text-muted">{m.label}</p>
      <div className="grid grid-cols-2 gap-4">
        {side(m.first, "first", n1)}
        {side(m.second, "second", n2)}
      </div>
    </li>
  );
}

function Result({ c, avatars }: { c: Compare; avatars: Record<string, string> }) {
  const n1 = c.first.name;
  const n2 = c.second.name;
  const wins1 = c.metrics.filter((m) => m.better === "first").length;
  const wins2 = c.metrics.filter((m) => m.better === "second").length;
  return (
    <>
      <section aria-labelledby="duelo" className="card border-t-4 border-t-gold-bg p-4 md:p-6">
        <h2 id="duelo" className="sr-only">
          {n1} contra {n2}
        </h2>
        <div className="grid items-center gap-4 md:grid-cols-[1fr_auto_1fr] md:gap-8">
          <Contender player={c.first} avatars={avatars} side="left" wins={wins1 >= wins2} />
          <div className="flex flex-col items-center gap-1 text-center">
            <span aria-hidden="true" className="num text-5xl leading-none text-muted">
              ×
            </span>
            <p className="text-base text-muted">
              Melhor em <b className={wins1 > wins2 ? "text-gold" : "text-fg"}>{wins1}</b> a{" "}
              <b className={wins2 > wins1 ? "text-gold" : "text-fg"}>{wins2}</b> métricas
            </p>
            {c.opponent_games > 0 && (
              <p className="text-base text-muted">
                Confrontos diretos: <b className="text-fg">{c.head_to_head.first}</b> a <b className="text-fg">{c.head_to_head.second}</b>
              </p>
            )}
          </div>
          <Contender player={c.second} avatars={avatars} side="right" wins={wins2 >= wins1} />
        </div>
      </section>

      <section aria-labelledby="carreira">
        <SectionTitle id="carreira" title="Comparação de carreira">
          Todas as partidas oficiais, sem limite semanal de XP. A estrela marca o melhor valor.
        </SectionTitle>
        <ul className="card divide-y divide-line-soft px-4 md:px-6" aria-label={`Comparação de carreira entre ${n1} e ${n2}`}>
          {c.metrics.map((m) => (
            <MetricRow key={m.key} m={m} n1={n1} n2={n2} />
          ))}
        </ul>
        <p className="mt-3 text-sm text-muted">O ADR acumulado usa o dano e os rounds disponíveis.</p>
      </section>

      <section aria-labelledby="comum">
        <SectionTitle id="comum" title="Partidas em comum" />
        <dl className="mb-4 grid gap-3 sm:grid-cols-3">
          <Stat label="Partidas em que os dois jogaram" value={num(c.shared_count)} />
          <Stat label="Em lados opostos" value={num(c.opponent_games)} />
          <Stat label="Como companheiros" value={num(c.teammate_games)} />
        </dl>

        {c.shared_count === 0 ? (
          <EmptyState>
            Eles ainda não disputaram nenhuma partida em comum. As estatísticas da carreira permanecem comparáveis.
          </EmptyState>
        ) : (
          <>
            <p className="mb-2 text-base">
              <b>Vitórias em confrontos diretos:</b> {n1} {c.head_to_head.first} × {c.head_to_head.second} {n2}
            </p>
            {c.opponent_games === 0 && (
              <p className="mb-4 text-sm text-muted">
                Os jogadores só foram companheiros de equipe ou não há identificação confiável dos lados. Não existe
                confronto direto registrado.
              </p>
            )}

            <details className="card p-4">
              <summary className="cursor-pointer text-xl font-bold">
                Ver as {c.shared_count} {c.shared_count === 1 ? "partida" : "partidas"} em comum
              </summary>
              <div className="mt-3">
                <TableWrap caption="Partidas em comum com kills e ADR de cada jogador">
                  <thead>
                    <tr>
                      <Th>Partida</Th>
                      <Th>Relação</Th>
                      <Th numeric>Kills · {n1}</Th>
                      <Th numeric>Kills · {n2}</Th>
                      <Th numeric>ADR · {n1}</Th>
                      <Th numeric>ADR · {n2}</Th>
                    </tr>
                  </thead>
                  <tbody>
                    {c.shared.map((s) => (
                      <tr key={s.match_id}>
                        <Td>
                          <Link href={`/partidas/mapa/${encodeURIComponent(s.match_id)}`}>
                            {s.map} · {dateBR(s.date)}
                          </Link>
                        </Td>
                        <Td>{s.relation}</Td>
                        <Td numeric>{num(s.first.kills)}</Td>
                        <Td numeric>{num(s.second.kills)}</Td>
                        <Td numeric>{num(s.first.adr, 1)}</Td>
                        <Td numeric>{num(s.second.adr, 1)}</Td>
                      </tr>
                    ))}
                  </tbody>
                </TableWrap>
                <p className="mt-3 text-sm text-muted">
                  Vitória em confronto direto é vitória da equipe, não abates de um jogador contra o outro.
                </p>
              </div>
            </details>

            <details className="card mt-4 p-4">
              <summary className="cursor-pointer text-xl font-bold">Gráfico: eliminações por mapa</summary>
              <div className="mt-3">
                <PairBars
                  caption={`Kills de ${n1} e ${n2} em cada partida em comum`}
                  nameA={n1}
                  nameB={n2}
                  unit="kills"
                  items={c.shared.map((s) => ({
                    id: s.match_id,
                    label: `${s.map} · ${dateBR(s.date)}`,
                    a: s.first.kills,
                    b: s.second.kills,
                  }))}
                />
              </div>
            </details>
          </>
        )}
      </section>
    </>
  );
}
