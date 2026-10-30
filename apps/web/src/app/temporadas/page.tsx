import Link from "next/link";
import { AchievementTabs } from "@/components/layout/SectionTabs";
import { Avatar } from "@/components/ui/Avatar";
import { Badge, type Tone } from "@/components/ui/Badge";
import { Card, EmptyState, SectionTitle } from "@/components/ui/Card";
import { LinkButton } from "@/components/ui/Button";
import { PageHeader } from "@/components/ui/PageHeader";
import { api, steamAvatars } from "@/lib/api";
import { dateBR, num, seasonSummary } from "@/lib/format";
import type { SeasonArchive, SeasonArchiveItem, SeasonStatus } from "@/lib/types";

export const metadata = {
  title: "Temporadas",
  description: "Arquivo de temporadas da EDB LEAGUE: períodos, números e títulos de cada uma.",
};

const STATUS: Record<SeasonStatus, { label: string; tone: Tone }> = {
  active: { label: "Em andamento", tone: "accent" },
  closed_pending: { label: "Aguardando homologação", tone: "neutral" },
  homologated: { label: "Homologada", tone: "gold" },
  upcoming: { label: "A iniciar", tone: "neutral" },
  unknown: { label: "Calendário a confirmar", tone: "neutral" },
};

const RANKING_NAME = { elite: "Ranking Elite", superacao: "Ranking Superação", xp: "Ranking XP" } as const;

function Highlights({ item, avatars }: { item: SeasonArchiveItem; avatars: Record<string, string> }) {
  const official = item.season.homologated;
  return (
    <ul className="grid gap-3 md:grid-cols-3" aria-label={official ? "Campeões oficiais" : "Líderes até agora"}>
      {item.highlights.map((h) => (
        <li key={h.title} className={official && h.title === "MVP" ? "card border-2 border-gold-bg p-4" : "card p-4"}>
          <p className="text-sm text-muted">
            <b className={official ? "text-gold" : "text-fg"}>{h.title}</b> · {RANKING_NAME[h.ranking]}
            {!official && " · parcial"}
          </p>
          <div className="mt-2 flex items-center gap-3">
            {h.player && <Avatar name={h.player.name} src={avatars[h.player.id]} size={44} level={null} decorative className="border-2" />}
            <p className="num text-3xl leading-tight break-words">
              {h.player ? (
                <Link href={`/jogadores/${encodeURIComponent(h.player.id)}`} className="text-fg no-underline hover:underline">
                  {h.player.name}
                </Link>
              ) : (
                "A definir"
              )}
            </p>
          </div>
          <p className="mt-1 text-sm text-muted">{h.detail}</p>
        </li>
      ))}
    </ul>
  );
}

export default async function SeasonsPage() {
  const [archive, avatars] = await Promise.all([api<SeasonArchive>("/seasons"), steamAvatars()]);

  return (
    <>
      <PageHeader
        title="Temporadas"
        subtitle="Cada ciclo da liga, do dia 19 ao dia 18, com os números e os títulos de cada uma."
        art="trophy"
      />
      <AchievementTabs current="/temporadas" />

      {archive.seasons.length === 0 ? (
        <EmptyState>Nenhuma temporada iniciada ainda.</EmptyState>
      ) : (
        <div className="flex flex-col gap-6">
          {archive.seasons.map((item) => {
            const { season } = item;
            const status = STATUS[season.status];
            const period = season.starts_on && season.ends_on ? `${dateBR(season.starts_on)} a ${dateBR(season.ends_on)}` : "Período a confirmar";
            return (
              <Card key={season.number} aria-labelledby={`temporada-${season.number}`}>
                <SectionTitle id={`temporada-${season.number}`} title={season.label}>
                  {period}
                </SectionTitle>
                <div className="mb-4 flex flex-wrap items-center gap-3">
                  <Badge tone={status.tone}>{status.label}</Badge>
                  <p className="text-base text-muted">{seasonSummary(season)}</p>
                </div>
                <dl className="mb-4 grid grid-cols-2 gap-3 md:grid-cols-4">
                  {[
                    ["Jogadores", item.counts.players],
                    ["Mapas", item.counts.matches],
                    ["Kills", item.counts.kills],
                    ["XP distribuído", item.counts.xp_distributed],
                  ].map(([label, value]) => (
                    <div key={label} className="card px-4 py-3">
                      <dt className="text-sm text-muted">{label}</dt>
                      <dd className="num text-3xl leading-none">{num(Number(value))}</dd>
                    </div>
                  ))}
                </dl>
                <Highlights item={item} avatars={avatars} />
                <div className="mt-4 flex flex-wrap gap-3">
                  <LinkButton href={`/rankings/elite?temporada=${season.number}`}>Ver rankings</LinkButton>
                  <LinkButton href={`/partidas?temporada=${season.number}`}>Ver partidas</LinkButton>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </>
  );
}
