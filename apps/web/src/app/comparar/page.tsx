import Link from "next/link";
import { Notice } from "@/components/ui/Notice";
import { PairBars } from "@/components/ui/Charts";
import { Button } from "@/components/ui/Button";
import { Card, EmptyState, SectionTitle } from "@/components/ui/Card";
import { SelectField } from "@/components/ui/Field";
import { PageHeader } from "@/components/ui/PageHeader";
import { TableWrap, Td, Th } from "@/components/ui/Table";
import { Stat } from "@/components/ui/Stat";
import { api, qs } from "@/lib/api";
import { dateBR, first, num } from "@/lib/format";
import type { Compare, Meta, PlayerListItem } from "@/lib/types";

export const metadata = { title: "Comparar jogadores" };

export default async function ComparePage({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const sp = await searchParams;
  const [meta, players] = await Promise.all([api<Meta>("/meta"), api<PlayerListItem[]>("/players")]);
  const sorted = [...players].sort((a, b) => a.name.localeCompare(b.name, "pt-BR"));

  const ids = new Set(sorted.map((p) => p.id));
  const askedA = first(sp.a);
  const askedB = first(sp.b);
  const a = askedA && ids.has(askedA) ? askedA : sorted[0]?.id;
  const b = askedB && ids.has(askedB) ? askedB : sorted.find((p) => p.id !== a)?.id;
  const same = a !== undefined && a === b;
  const comparison = a && b && !same ? await api<Compare>(`/compare${qs({ a, b })}`) : null;

  return (
    <>
      <PageHeader
        title="Comparar jogadores"
        subtitle="Análise lado a lado: desempenho, vitórias e confrontos da liga."
        art="duel"
        counts={{ players: meta.counts.players, matches: meta.counts.matches, maps: meta.counts.maps }}
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

          {comparison && <Result c={comparison} />}
        </>
      )}
    </>
  );
}

function Result({ c }: { c: Compare }) {
  const n1 = c.first.name;
  const n2 = c.second.name;
  return (
    <>
      <section aria-labelledby="carreira">
        <SectionTitle id="carreira" title="Comparação de carreira" />
        <TableWrap caption={`Comparação de carreira entre ${n1} e ${n2}`}>
          <thead>
            <tr>
              <Th>Métrica</Th>
              <Th numeric>
                <Link href={`/jogadores/${encodeURIComponent(c.first.id)}`}>{n1}</Link>
              </Th>
              <Th numeric>
                <Link href={`/jogadores/${encodeURIComponent(c.second.id)}`}>{n2}</Link>
              </Th>
            </tr>
          </thead>
          <tbody>
            {c.metrics.map((m) => (
              <tr key={m.key}>
                <Td className="font-bold">{m.label}</Td>
                {(["first", "second"] as const).map((side) => {
                  const best = m.better === side;
                  return (
                    <Td key={side} numeric className={best ? "font-extrabold text-gold" : undefined}>
                      {best && (
                        <>
                          <span aria-hidden="true">★ </span>
                          <span className="sr-only">Melhor: </span>
                        </>
                      )}
                      {num(m[side], m.decimals, m.suffix)}
                    </Td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </TableWrap>
        <p className="mt-3 text-sm text-muted">
          Comparação de todas as partidas oficiais, sem limite semanal de XP. O ADR acumulado utiliza dano e rounds
          disponíveis. A estrela marca o melhor valor.
        </p>
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

            <Card className="mb-4">
              <h3 className="mb-3 text-xl font-bold">Eliminações por mapa</h3>
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
            </Card>

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
          </>
        )}
      </section>
    </>
  );
}
