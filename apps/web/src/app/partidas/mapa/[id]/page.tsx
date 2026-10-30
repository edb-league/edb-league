import Link from "next/link";
import { OutcomeBadge } from "@/components/ui/Badge";
import { Card, EmptyState, SectionTitle } from "@/components/ui/Card";
import { Tabs } from "@/components/ui/Tabs";
import { TableWrap, Td, Th } from "@/components/ui/Table";
import { apiOrNotFound } from "@/lib/api";
import { first, num, parseSeason, seasonQuery } from "@/lib/format";
import type { MatchDetail } from "@/lib/types";
import { NoData } from "@/components/ui/NoData";
import { MapTile } from "@/components/ui/MapTile";

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  try {
    const d = await apiOrNotFound<MatchDetail>(`/matches/${encodeURIComponent(id)}`);
    const m = d.match;
    const score = m.score_left !== null && m.score_right !== null ? `${m.left} ${m.score_left} × ${m.score_right} ${m.right}` : `${m.left} × ${m.right}`;
    return { title: `${m.map} · ${m.date_label}`, description: `${score} em ${m.map}, ${m.date_label}. Estatísticas completas na EDB LEAGUE.` };
  } catch {
    return { title: "Partida" };
  }
}

export default async function MatchDetailPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { id } = await params;
  const sp = await searchParams;
  const detail = await apiOrNotFound<MatchDetail>(`/matches/${encodeURIComponent(id)}`);
  const season = parseSeason(sp.temporada) ?? detail.season ?? undefined;
  const confronto = first(sp.confronto) ?? detail.series_id ?? undefined;
  const back = `/partidas${seasonQuery(season, { confronto })}${confronto ? `#confronto-${confronto}` : ""}`;
  const m = detail.match;
  const score = m.verified ? `${m.score_left} : ${m.score_right}` : null;

  return (
    <>
      <p>
        <Link href={back} className="link-cta">
          ← Voltar às partidas
        </Link>
      </p>

      <header className="card overflow-hidden border-t-4 border-t-gold-bg">
        <MapTile map={m.map} className="px-5 py-5 md:px-6 md:py-6">
          <p className="inline-block rounded-full bg-surface/80 px-3 py-0.5 text-base text-muted">Partida · {m.date_label}</p>
          <h1 className="mt-2 text-5xl leading-none">
            {m.map}
            <span className="sr-only">: </span>
          </h1>
        </MapTile>
        <div className="p-5 md:px-6">
          <p className="text-xl font-bold">
            {m.left} <span className="num mx-2 text-3xl text-gold">{score ?? <NoData />}</span> {m.right}
          </p>
          <p className="mt-1 text-base text-muted">
            {m.verified ? "Placar verificado" : "Placar ainda não verificado"} · Fonte: {detail.source}
            {detail.rounds_total ? ` · ${detail.rounds_total} rounds` : ""}
          </p>
        </div>
      </header>

      <section aria-labelledby="placar">
        <SectionTitle id="placar" title="Placar da partida" />
        {detail.teams.length === 0 ? (
          <EmptyState>Esta partida ainda não tem estatísticas por jogador.</EmptyState>
        ) : (
          <div className="flex flex-col gap-6">
            {detail.teams.map((team) => (
              <div key={team.name}>
                <div className="mb-2 flex flex-wrap items-center justify-between gap-2 rounded-lg border border-line-soft bg-surface-2 px-4 py-3">
                  <h3 className="text-lg font-bold">{team.name}</h3>
                  <p className="flex items-center gap-3 text-base text-muted">
                    <OutcomeBadge outcome={team.outcome} />
                    {team.players} jogadores · {team.kills} kills
                  </p>
                </div>
                <TableWrap caption={`Placar da equipe ${team.name}`}>
                  <thead>
                    <tr>
                      <Th>Jogador</Th>
                      <Th numeric>K</Th>
                      <Th numeric>A</Th>
                      <Th numeric>D</Th>
                      <Th numeric>K/D</Th>
                      <Th numeric>ADR</Th>
                    </tr>
                  </thead>
                  <tbody>
                    {team.rows.map((r) => (
                      <tr key={r.player}>
                        <Td className="font-bold">{r.player}</Td>
                        <Td numeric>{num(r.k)}</Td>
                        <Td numeric>{num(r.a)}</Td>
                        <Td numeric>{num(r.d)}</Td>
                        <Td numeric>{num(r.kd, 2)}</Td>
                        <Td numeric>{num(r.adr, 1)}</Td>
                      </tr>
                    ))}
                  </tbody>
                </TableWrap>
              </div>
            ))}
          </div>
        )}
      </section>

      <Card aria-labelledby="detalhadas">
        <SectionTitle id="detalhadas" title="Estatísticas detalhadas" />
        <Tabs
          label="Tipo de estatística"
          tabs={[
            {
              value: "geral",
              label: "Geral",
              content: (
                <>
                  <TableWrap caption="Estatísticas gerais por jogador">
                    <thead>
                      <tr>
                        <Th>Jogador</Th>
                        <Th numeric>Kills</Th>
                        <Th numeric>Mortes</Th>
                        <Th numeric>Assist.</Th>
                        <Th numeric>Dano</Th>
                        <Th numeric>Rounds</Th>
                        <Th>Resultado</Th>
                        <Th numeric>HLTV</Th>
                        <Th numeric>KAST (%)</Th>
                        <Th numeric>Open kills</Th>
                        <Th numeric>Trade kills</Th>
                        <Th numeric>ADR (SCOPE)</Th>
                        <Th numeric>Dif. ADR</Th>
                      </tr>
                    </thead>
                    <tbody>
                      {detail.general.map((r) => (
                        <tr key={r.player}>
                          <Td className="font-bold">{r.player}</Td>
                          <Td numeric>{num(r.kills)}</Td>
                          <Td numeric>{num(r.deaths)}</Td>
                          <Td numeric>{num(r.assists)}</Td>
                          <Td numeric>{num(r.damage)}</Td>
                          <Td numeric>{num(r.rounds)}</Td>
                          <Td>{r.won === true ? "Vitória" : r.won === false ? "Derrota" : <NoData />}</Td>
                          <Td numeric>{num(r.rating, 2)}</Td>
                          <Td numeric>{num(r.kast, 1)}</Td>
                          <Td numeric>{num(r.open_kills)}</Td>
                          <Td numeric>{num(r.trade_kills)}</Td>
                          <Td numeric>{num(r.adr_reported, 1)}</Td>
                          <Td numeric>{num(r.adr_difference, 1)}</Td>
                        </tr>
                      ))}
                    </tbody>
                  </TableWrap>
                  <p className="mt-3 text-sm text-muted">
                    ADR da fonte SCOPE.GG, se informado. Rounds inferidos quando o placar não mostra o total.
                  </p>
                </>
              ),
            },
            {
              value: "mira",
              label: "Mira",
              content: detail.aim.length ? (
                <TableWrap caption="Estatísticas de mira por jogador">
                  <thead>
                    <tr>
                      <Th>Jogador</Th>
                      <Th numeric>Tempo p/ kill (s)</Th>
                      <Th numeric>Tempo de dano (s)</Th>
                      <Th numeric>Precisão (%)</Th>
                      <Th numeric>HS rifle (%)</Th>
                      <Th numeric>HS pistola (%)</Th>
                      <Th numeric>1º disparo (%)</Th>
                    </tr>
                  </thead>
                  <tbody>
                    {detail.aim.map((r) => (
                      <tr key={r.player}>
                        <Td className="font-bold">{r.player}</Td>
                        <Td numeric>{num(r.time_to_kill_seconds, 2)}</Td>
                        <Td numeric>{num(r.damage_time_seconds, 2)}</Td>
                        <Td numeric>{num(r.aim_accuracy_pct, 1)}</Td>
                        <Td numeric>{num(r.rifle_hs_pct, 1)}</Td>
                        <Td numeric>{num(r.pistol_hs_pct, 1)}</Td>
                        <Td numeric>{num(r.first_bullet_accuracy_pct, 1)}</Td>
                      </tr>
                    ))}
                  </tbody>
                </TableWrap>
              ) : (
                <EmptyState>Sem dados de mira desta partida.</EmptyState>
              ),
            },
            {
              value: "utilitarias",
              label: "Utilitárias",
              content: detail.utility.length ? (
                <TableWrap caption="Estatísticas de utilitárias por jogador">
                  <thead>
                    <tr>
                      <Th>Jogador</Th>
                      <Th numeric>Flash assists</Th>
                      <Th numeric>Flash assists úteis</Th>
                      <Th numeric>Inimigos cegados</Th>
                      <Th numeric>Flash (s)</Th>
                      <Th numeric>Dano de granada</Th>
                      <Th numeric>Smokes</Th>
                      <Th numeric>Atingidos por fogo</Th>
                      <Th numeric>Atingidos por HE</Th>
                    </tr>
                  </thead>
                  <tbody>
                    {detail.utility.map((r) => (
                      <tr key={r.player}>
                        <Td className="font-bold">{r.player}</Td>
                        <Td numeric>{num(r.flash_assists)}</Td>
                        <Td numeric>{num(r.impactful_flash_assists)}</Td>
                        <Td numeric>{num(r.enemies_flashed)}</Td>
                        <Td numeric>{num(r.total_flash_duration_seconds, 1)}</Td>
                        <Td numeric>{num(r.grenade_damage)}</Td>
                        <Td numeric>{num(r.smokes_used)}</Td>
                        <Td numeric>{num(r.enemies_damaged_fire)}</Td>
                        <Td numeric>{num(r.enemies_damaged_he)}</Td>
                      </tr>
                    ))}
                  </tbody>
                </TableWrap>
              ) : (
                <EmptyState>Sem dados de granadas desta partida.</EmptyState>
              ),
            },
          ]}
        />
      </Card>

      <p className="text-sm text-muted">
        ID: {m.id.slice(0, 20)}… · Rounds: {detail.rounds_total ?? <NoData />}
        {detail.coverage.players > 0 &&
          ` · Estatísticas: ${detail.coverage.players} jogadores, ${detail.coverage.kills} kills, mira ${detail.coverage.aim}/${detail.coverage.players}, utilitárias ${detail.coverage.grenades}/${detail.coverage.players}`}
        {detail.notes ? ` · ${detail.notes}` : ""}
      </p>
    </>
  );
}
