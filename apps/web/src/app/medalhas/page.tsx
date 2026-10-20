import Link from "next/link";
import { TIER_LABEL, TierBadge } from "@/components/players/MedalCard";
import { Badge } from "@/components/ui/Badge";
import { SectionTitle } from "@/components/ui/Card";
import { AchievementTabs } from "@/components/layout/SectionTabs";
import { PageHeader } from "@/components/ui/PageHeader";
import { Stat, StatGrid } from "@/components/ui/Stat";
import { api } from "@/lib/api";
import { num, plural } from "@/lib/format";
import type { MedalCatalogue, Meta } from "@/lib/types";

export const metadata = { title: "Medalhas" };

const TIER_TEXT = {
  bronze: "Os primeiros marcos da jornada.",
  silver: "Constância e destaque nas partidas.",
  gold: "Feitos raros que merecem reconhecimento.",
} as const;

export default async function MedalsPage() {
  const [meta, cat] = await Promise.all([api<Meta>("/meta"), api<MedalCatalogue>("/medals")]);
  const tiers = ["bronze", "silver", "gold"] as const;

  return (
    <>
      <PageHeader
        title="Medalhas"
        subtitle="Reconhecimento para quem faz a diferença. Conquiste, evolua e deixe sua marca."
        art="medals"
        counts={{ players: meta.counts.players, matches: meta.counts.matches, maps: meta.counts.maps }}
      />
      <AchievementTabs current="/medalhas" />

      <section aria-labelledby="resumo">
        <h2 id="resumo" className="sr-only">Resumo</h2>
        <StatGrid>
          <Stat label="Medalhas disponíveis" value={num(cat.summary.available)} />
          <Stat label="Jogadores premiados" value={num(cat.summary.honored_players)} />
          <Stat label="Níveis de conquista" value={num(cat.summary.tiers)} />
          <Stat label="Medalhas conquistadas" value={num(cat.summary.earned_total)} />
        </StatGrid>
      </section>

      <section aria-labelledby="categorias">
        <SectionTitle id="categorias" title="Categorias de medalhas" />
        <ul className="grid gap-3 md:grid-cols-3">
          {tiers.map((tier) => (
            <li key={tier} className="card p-5">
              <TierBadge tier={tier} />
              <p className="mt-2 text-lg font-bold">{TIER_LABEL[tier]}</p>
              <p className="text-base text-muted">
                {plural(cat.medals.filter((m) => m.tier === tier).length, "medalha", "medalhas")} · {TIER_TEXT[tier]}
              </p>
            </li>
          ))}
        </ul>
      </section>

      <section aria-labelledby="catalogo">
        <SectionTitle id="catalogo" title="Medalhas da EDB LEAGUE">
          Vencedores vinculados ao cadastro dos jogadores. Todos os números refletem partidas registradas.
        </SectionTitle>
        <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {cat.medals.map((m) => (
            <li key={m.id} className={`card flex flex-col gap-2 p-5 ${m.holders.length ? "border-gold" : ""}`}>
              <div className="flex items-center justify-between gap-2">
                <TierBadge tier={m.tier} />
                {m.holders.length > 0 && (
                  <Badge tone="win">
                    <span aria-hidden="true">✓</span> Conquistada
                  </Badge>
                )}
              </div>
              <h3 className="text-lg font-bold">{m.name}</h3>
              <p className="text-base text-muted">{m.description}</p>
              <p className="text-sm text-muted">
                {m.holders.length} {m.holders.length === 1 ? "jogador conquistou" : "jogadores conquistaram"}
              </p>
              {m.holders.length > 0 && (
                <p className="text-base">
                  {m.holders.slice(0, 8).map((h, i) => (
                    <span key={h.id}>
                      {i > 0 && " · "}
                      <Link href={`/jogadores/${encodeURIComponent(h.id)}`}>{h.name}</Link>
                    </span>
                  ))}
                  {m.holders.length > 8 && ` · e mais ${m.holders.length - 8}`}
                </p>
              )}
            </li>
          ))}
        </ul>
        <p className="mt-4 text-sm text-muted">
          Abra o perfil de um jogador para ver as medalhas conquistadas e seu progresso individual.
        </p>
      </section>
    </>
  );
}
