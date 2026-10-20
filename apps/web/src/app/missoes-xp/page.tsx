import { RankingList } from "@/components/rankings/RankingList";
import { SeasonBar } from "@/components/layout/SeasonBar";
import { Card, SectionTitle } from "@/components/ui/Card";
import { PageHeader } from "@/components/ui/PageHeader";
import { Stat } from "@/components/ui/Stat";
import { api, qs } from "@/lib/api";
import { num } from "@/lib/format";
import { seasonContext } from "@/lib/season";
import type { Missions } from "@/lib/types";

export const metadata = { title: "Missões e XP" };

export default async function MissionsPage({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const { meta, season } = await seasonContext((await searchParams).temporada);
  const missions = await api<Missions>(`/missions${qs({ season })}`);

  return (
    <>
      <PageHeader
        title="Missões e conquistas"
        subtitle="Todo nível tem uma meta. O prêmio é igual; o desafio é proporcional."
        art="xp"
        counts={{ players: meta.counts.players, matches: meta.counts.matches, maps: meta.counts.maps }}
      />
      <SeasonBar meta={meta} season={season} path="/missoes-xp" />

      <Card aria-labelledby="meta-semanal">
        <SectionTitle id="meta-semanal" title="Meta semanal: kills por round" />
        <dl className="grid grid-cols-2 gap-3 sm:grid-cols-5">
          {missions.targets.map((t) => (
            <Stat key={t.stars} label={`${t.stars} ${t.stars === 1 ? "estrela" : "estrelas"}`} value={`${num(t.kpr, 2)} KPR`} />
          ))}
        </dl>
        <ul className="mt-4 list-disc space-y-1 pl-5 text-base text-muted">
          <li>Concluir uma partida de pelo menos 8 rounds com KPR acima da meta rende 100 XP, uma vez por semana.</li>
          <li>Presença: +40 XP por mapa; vitória: +20 XP; até 6 mapas na temporada, além de até 100 XP de missão por semana.</li>
        </ul>
      </Card>

      <section aria-labelledby="xp-ranking">
        <SectionTitle id="xp-ranking" title="Ranking de experiência" />
        <RankingList ranking={missions.xp} />
        <p className="mt-4 max-w-prose text-base text-muted">
          Os únicos títulos competitivos oficiais são MVP Elite, Revelação Superação e Xinxa XP. Os resultados serão
          homologados após o encerramento.
        </p>
      </section>
    </>
  );
}
