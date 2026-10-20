import clsx from "clsx";
import { Badge, type Tone } from "@/components/ui/Badge";
import { Progress } from "@/components/ui/Charts";
import { num } from "@/lib/format";
import type { Medal } from "@/lib/types";

export const TIER_LABEL = { bronze: "Bronze", silver: "Prata", gold: "Ouro" } as const;
export const TIER_TONE: Record<Medal["tier"], Tone> = { bronze: "loss", silver: "neutral", gold: "gold" };

export function TierBadge({ tier }: { tier: Medal["tier"] }) {
  return <Badge tone={TIER_TONE[tier]}>{TIER_LABEL[tier]}</Badge>;
}

/** Medalha com progresso individual (perfil do jogador). */
export function MedalCard({ medal }: { medal: Medal }) {
  return (
    <li className={clsx("card flex flex-col gap-2 p-4", medal.earned && "border-gold")}>
      <div className="flex items-center justify-between gap-2">
        <TierBadge tier={medal.tier} />
        {medal.earned && (
          <Badge tone="win">
            <span aria-hidden="true">✓</span> Conquistada
          </Badge>
        )}
      </div>
      <h4 className="text-lg font-bold">{medal.name}</h4>
      <p className="text-base text-muted">{medal.description}</p>
      {medal.progress !== null ? (
        <div className="mt-auto flex flex-col gap-1">
          <Progress value={medal.progress} label={`Progresso de ${medal.name}`} />
          <p className="tabular text-sm text-muted">
            {num(medal.current)} / {num(medal.target)}
          </p>
        </div>
      ) : (
        <p className="mt-auto text-sm text-muted">Sem dados disponíveis para esta métrica</p>
      )}
    </li>
  );
}
