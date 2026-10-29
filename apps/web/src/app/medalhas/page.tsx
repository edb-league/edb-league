import clsx from "clsx";
import Link from "next/link";
import { HolderStack } from "@/components/players/HolderStack";
import { MedalShape, TIER_LABEL, TierBadge } from "@/components/players/MedalCard";
import { Badge } from "@/components/ui/Badge";
import { SectionTitle } from "@/components/ui/Card";
import { AchievementTabs } from "@/components/layout/SectionTabs";
import { PageHeader } from "@/components/ui/PageHeader";
import { api, steamAvatars } from "@/lib/api";
import { num, plural } from "@/lib/format";
import type { MedalCatalogue } from "@/lib/types";
import { Icon } from "@/components/ui/Icon";

export const metadata = { title: "Medalhas" };

export default async function MedalsPage({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const [cat, sp, avatars] = await Promise.all([api<MedalCatalogue>("/medals"), searchParams, steamAvatars()]);
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
                      "press lift inline-flex min-h-11 items-center rounded-lg border px-4 text-base font-bold no-underline",
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
          {shown.map((m) => {
            const earned = m.holders.length > 0;
            return (
              <li key={m.id} className={`card flex gap-4 p-4 ${earned ? "border-gold" : ""}`}>
                <MedalShape tier={m.tier} earned={earned} size={56} />
                <div className="flex min-w-0 flex-1 flex-col gap-1.5">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <TierBadge tier={m.tier} />
                    {earned && (
                      <Badge tone="win">
                        <Icon name="check" /> Conquistada
                      </Badge>
                    )}
                  </div>
                  <h3 className="text-xl leading-tight font-bold">{m.name}</h3>
                  <p className="text-base text-muted">{m.description}</p>
                  <div className="mt-auto flex flex-col gap-1.5 pt-1">
                    <HolderStack holders={m.holders} avatars={avatars} />
                    <p className="text-sm text-muted">
                      {earned
                        ? `${m.holders.length} ${m.holders.length === 1 ? "jogador conquistou" : "jogadores conquistaram"}`
                        : "Ninguém conquistou ainda"}
                    </p>
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
        <p className="mt-4 text-sm text-muted">
          Abra o perfil de um jogador para ver as medalhas conquistadas e seu progresso individual.
        </p>
      </section>
    </>
  );
}
