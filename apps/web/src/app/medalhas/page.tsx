import clsx from "clsx";
import Link from "next/link";
import { TIER_LABEL, TierBadge } from "@/components/players/MedalCard";
import { Badge } from "@/components/ui/Badge";
import { SectionTitle } from "@/components/ui/Card";
import { AchievementTabs } from "@/components/layout/SectionTabs";
import { PageHeader } from "@/components/ui/PageHeader";
import { api } from "@/lib/api";
import { num, plural } from "@/lib/format";
import type { MedalCatalogue, Meta } from "@/lib/types";

export const metadata = { title: "Medalhas" };

export default async function MedalsPage({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const [meta, cat, sp] = await Promise.all([api<Meta>("/meta"), api<MedalCatalogue>("/medals"), searchParams]);
  const tiers = ["bronze", "silver", "gold"] as const;
  const raw = Array.isArray(sp.faixa) ? sp.faixa[0] : sp.faixa;
  const tier = tiers.find((t) => t === raw) ?? null;
  const shown = tier ? cat.medals.filter((m) => m.tier === tier) : cat.medals;
  const filters = [
    { key: null, label: "Todas", count: cat.medals.length },
    ...tiers.map((t) => ({ key: t, label: TIER_LABEL[t], count: cat.medals.filter((m) => m.tier === t).length })),
  ];

  return (
    <>
      <PageHeader
        title="Medalhas"
        subtitle="Reconhecimento para quem faz a diferença. Conquiste, evolua e deixe sua marca."
        art="medals"
        counts={{ players: meta.counts.players, matches: meta.counts.matches, maps: meta.counts.maps }}
      />
      <AchievementTabs current="/medalhas" />

      <section aria-labelledby="catalogo">
        <SectionTitle id="catalogo" title="Medalhas da EDB LEAGUE">
          {plural(cat.summary.available, "medalha disponível", "medalhas disponíveis")},{" "}
          {plural(cat.summary.earned_total, "conquista", "conquistas")} de {plural(cat.summary.honored_players, "jogador", "jogadores")}.
        </SectionTitle>
        <nav aria-label="Filtrar por faixa" className="mb-4">
          <ul className="flex flex-wrap gap-2">
            {filters.map((f) => {
              const active = f.key === tier;
              return (
                <li key={f.label}>
                  <Link
                    href={f.key ? `/medalhas?faixa=${f.key}` : "/medalhas"}
                    aria-current={active ? "page" : undefined}
                    className={clsx(
                      "inline-flex min-h-11 items-center rounded-lg border px-4 text-base font-bold no-underline",
                      active ? "border-gold-bg bg-gold-bg text-on-gold" : "border-line bg-surface text-fg hover:bg-surface-2",
                    )}
                  >
                    {f.label} ({f.count})
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
        <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {shown.map((m) => (
            <li key={m.id} className={`card flex flex-col gap-1.5 p-4 ${m.holders.length ? "border-gold" : ""}`}>
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
                  {m.holders.slice(0, 3).map((h, i) => (
                    <span key={h.id}>
                      {i > 0 && " · "}
                      <Link href={`/jogadores/${encodeURIComponent(h.id)}`}>{h.name}</Link>
                    </span>
                  ))}
                  {m.holders.length > 3 && ` · e mais ${m.holders.length - 3}`}
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
