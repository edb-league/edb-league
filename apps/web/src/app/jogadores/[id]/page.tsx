import Image from "next/image";
import Link from "next/link";
import { Evolution } from "@/components/players/Evolution";
import { MedalCard } from "@/components/players/MedalCard";
import { Badge, OutcomeBadge } from "@/components/ui/Badge";
import { Card, EmptyState, SectionTitle } from "@/components/ui/Card";
import { Stat, StatGrid } from "@/components/ui/Stat";
import { TableWrap, Td, Th } from "@/components/ui/Table";
import { apiOrNotFound } from "@/lib/api";
import { dateBR, hoursLabel, num } from "@/lib/format";
import type { PlayerDetail } from "@/lib/types";
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

export default async function PlayerPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const d = await apiOrNotFound<PlayerDetail>(`/players/${encodeURIComponent(id)}`);
  const { player, steam, summary } = d;
  const games = summary.games;
  const earned = d.medals.filter((m) => m.earned);
  const locked = d.medals.filter((m) => !m.earned);

  return (
    <>
      <p>
        <Link href="/jogadores" className="inline-flex min-h-11 items-center text-base font-bold">
          ← Todos os jogadores
        </Link>
      </p>

      <header className="card p-5 md:p-6">
        <div className="flex flex-wrap items-center gap-5">
          {steam.avatar ? (
            <Image
              src={steam.avatar}
              alt={`Foto de ${player.name}`}
              width={96}
              height={96}
              unoptimized
              className="size-24 rounded-full border-2 border-line object-cover"
            />
          ) : (
            <Silhouette />
          )}
          <div className="min-w-0">
            <p className="kicker">Perfil do jogador</p>
            <h1 className="text-3xl font-extrabold break-words">{player.name}</h1>
            <p className="mt-1 flex flex-wrap items-center gap-2 text-base text-muted">
              Nível {player.level}
              {!player.is_active && <Badge>Fora do elenco ativo</Badge>}
              {steam.persona && <span>· Steam: {steam.persona}</span>}
            </p>
            <p className="mt-2 flex items-baseline gap-2">
              <b className="tabular text-2xl text-gold">{hoursLabel(steam.hours)}</b>
              <span className="text-sm font-bold text-muted">HORAS DE CS</span>
            </p>
            {steam.note && <p className="text-sm text-muted">{steam.note}</p>}
          </div>
        </div>

        <StatGrid className="mt-6 border-t border-line-soft pt-5">
          <Stat label="Partidas" value={num(games)} />
          <Stat label="Vitórias" value={games ? num(summary.wins) : <NoData />} />
          <Stat label="Aproveitamento" value={summary.win_rate !== null ? num(summary.win_rate, 0, "%") : <NoData />} />
          <Stat label="Kills" value={games ? num(summary.kills) : <NoData />} />
          <Stat label="Mortes" value={games ? num(summary.deaths) : <NoData />} />
          <Stat label="Assistências" value={games ? num(summary.assists) : <NoData />} />
          <Stat label="K/D" value={num(summary.kd, 2)} />
          <Stat label="ADR" value={num(summary.adr, 1)} />
        </StatGrid>
      </header>

      <Card aria-labelledby="evolucao">
        <SectionTitle id="evolucao" title="Evolução por partida" />
        {d.matches.length ? <Evolution matches={d.matches} /> : <EmptyState>Este jogador ainda não tem partidas registradas.</EmptyState>}
      </Card>

      <section aria-labelledby="medalhas">
        <SectionTitle id="medalhas" title="Medalhas">
          {earned.length} de {d.medals.length} medalhas conquistadas
        </SectionTitle>
        {earned.length > 0 && (
          <>
            <h3 className="mb-2 text-lg font-bold">Conquistadas</h3>
            <ul className="mb-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {earned.map((m) => (
                <MedalCard key={m.id} medal={m} />
              ))}
            </ul>
          </>
        )}
        <h3 className="mb-2 text-lg font-bold">Próximos desafios</h3>
        {locked.length ? (
          <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {locked.map((m) => (
              <MedalCard key={m.id} medal={m} />
            ))}
          </ul>
        ) : (
          <p className="text-base text-muted">Todas as medalhas foram conquistadas.</p>
        )}
      </section>

      <section aria-labelledby="historico">
        <SectionTitle id="historico" title="Histórico de partidas" />
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
                  <Td>{m.map}</Td>
                  <Td>{m.played_nick}</Td>
                  <Td>
                    <OutcomeBadge outcome={m.result} />
                  </Td>
                  <Td numeric>{num(m.kills)}</Td>
                  <Td numeric>{num(m.deaths)}</Td>
                  <Td numeric>{num(m.assists)}</Td>
                  <Td numeric>{num(m.kd, 2)}</Td>
                  <Td numeric>{num(m.adr, 1)}</Td>
                  <Td numeric>{num(m.rating, 2)}</Td>
                </tr>
              ))}
            </tbody>
          </TableWrap>
        ) : (
          <EmptyState>Sem partidas.</EmptyState>
        )}
        <p className="mt-3 text-sm text-muted">
          Os totais usam todas as partidas. O ADR acumulado é calculado por dano e rounds; partidas com rounds estimados
          podem afetá-lo.
        </p>
      </section>
    </>
  );
}
