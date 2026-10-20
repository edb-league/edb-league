import Link from "next/link";
import { AchievementTabs } from "@/components/layout/SectionTabs";
import { SeasonBar } from "@/components/layout/SeasonBar";
import { Card, SectionTitle } from "@/components/ui/Card";
import { LevelBadge } from "@/components/ui/LevelBadge";
import { PageHeader } from "@/components/ui/PageHeader";
import { Stat } from "@/components/ui/Stat";
import { TableWrap, Td, Th } from "@/components/ui/Table";
import { api, qs } from "@/lib/api";
import { num, seasonQuery } from "@/lib/format";
import { seasonContext } from "@/lib/season";
import type { Missions } from "@/lib/types";

export const metadata = { title: "Missões e XP" };

export default async function MissionsPage({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const { meta, season } = await seasonContext((await searchParams).temporada);
  const missions = await api<Missions>(`/missions${qs({ season })}`);
  const top = missions.xp.rows.slice(0, 5);

  return (
    <>
      <PageHeader
        title="Missões e conquistas"
        subtitle="Todo nível tem uma meta. O prêmio é igual; o desafio é proporcional."
        art="xp"
        counts={{ players: meta.counts.players, matches: meta.counts.matches, maps: meta.counts.maps }}
      />
      <AchievementTabs current="/missoes-xp" />
      <SeasonBar meta={meta} season={season} path="/missoes-xp" />

      <Card aria-labelledby="meta-semanal">
        <SectionTitle id="meta-semanal" title="Meta semanal: kills por round">
          Concluir uma partida de pelo menos 8 rounds com KPR acima da meta rende 100 XP, uma vez por semana.
        </SectionTitle>
        <dl className="grid grid-cols-2 gap-3 sm:grid-cols-5">
          {missions.targets.map((t) => (
            <Stat key={t.stars} label={`${t.stars} ${t.stars === 1 ? "estrela" : "estrelas"}`} value={`${num(t.kpr, 2)} KPR`} />
          ))}
        </dl>
        <p className="mt-4 text-base text-muted">
          Presença, vitórias e o limite de XP por temporada estão no{" "}
          <Link href="/regulamento#xp">Regulamento</Link>.
        </p>
      </Card>

      <section aria-labelledby="xp-ranking">
        <SectionTitle id="xp-ranking" title="Quem lidera em XP">
          Os cinco primeiros do ranking de experiência desta temporada.
        </SectionTitle>
        {top.length ? (
          <TableWrap caption="Cinco primeiros do ranking de experiência">
            <thead>
              <tr>
                <Th>#</Th>
                <Th>Jogador</Th>
                <Th>Nível</Th>
                <Th numeric>Partidas</Th>
                <Th numeric>XP</Th>
              </tr>
            </thead>
            <tbody>
              {top.map((r) => (
                <tr key={r.player_id}>
                  <Td className="num text-2xl text-muted">{r.rank}</Td>
                  <Td className="font-bold">
                    <Link href={`/jogadores/${encodeURIComponent(r.player_id)}`} className="text-fg">{r.name}</Link>
                  </Td>
                  <Td><LevelBadge level={r.level} /></Td>
                  <Td numeric>{num(r.matches)}</Td>
                  <Td numeric className="num text-2xl text-gold">{num(r.xp)}</Td>
                </tr>
              ))}
            </tbody>
          </TableWrap>
        ) : (
          <p className="text-base text-muted">O ranking aparece após as primeiras partidas.</p>
        )}
        <p className="mt-3">
          <Link href={`/rankings/xp${seasonQuery(season)}`} className="inline-flex min-h-11 items-center text-base font-bold">
            Ver o ranking XP completo →
          </Link>
        </p>
      </section>
    </>
  );
}
