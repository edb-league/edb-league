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

/** Formas diferentes por faixa (hexágono, escudo, estrela): a forma também diz o nível. */
const SHAPES = {
  bronze: "M22 3 L39 12.5 V31.5 L22 41 L5 31.5 V12.5 Z",
  silver: "M22 3 L39 9 V22 C39 32 32 38 22 42 C12 38 5 32 5 22 V9 Z",
  gold: "M22 2 L28 16 L43 17.5 L32 27.5 L35 42 L22 34.5 L9 42 L12 27.5 L1 17.5 L16 16 Z",
} as const;
const SHAPE_COLOR = { bronze: "text-loss", silver: "text-muted", gold: "text-gold" } as const;

export function MedalShape({ tier, earned, size = 44 }: { tier: Medal["tier"]; earned: boolean; size?: number }) {
  return (
    <svg aria-hidden="true" viewBox="0 0 44 44" width={size} height={size} className={clsx("shrink-0", SHAPE_COLOR[tier])}>
      <path
        d={SHAPES[tier]}
        fill={earned ? "currentColor" : "none"}
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinejoin="round"
        strokeDasharray={earned ? undefined : "4 3"}
      />
    </svg>
  );
}

/** Medalha com progresso individual (perfil do jogador). */
export function MedalCard({ medal }: { medal: Medal }) {
  return (
    <li className={clsx("card flex gap-3 p-4", medal.earned && "border-gold-bg")}>
      <MedalShape tier={medal.tier} earned={medal.earned} />
      <div className="flex min-w-0 flex-1 flex-col gap-2">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <TierBadge tier={medal.tier} />
          {medal.earned && (
            <Badge tone="win">
              <span aria-hidden="true">✓</span> Conquistada
            </Badge>
          )}
        </div>
        <h4 className="text-xl font-bold">{medal.name}</h4>
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
      </div>
    </li>
  );
}
