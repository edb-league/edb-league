import clsx from "clsx";

/**
 * Selo de nível (1 a 10). A faixa muda a forma e a cor (aço, azul, ouro, ouro com anel),
 * mas o número sempre aparece em texto.
 */
export const LEVEL_TIERS = [
  "bg-[var(--lv1-bg)] text-[var(--lv1-fg)]",
  "bg-[var(--lv2-bg)] text-[var(--lv2-fg)]",
  "bg-[var(--lv3-bg)] text-[var(--lv3-fg)]",
  "bg-[var(--lv4-bg)] text-[var(--lv4-fg)] ring-2 ring-[var(--lv4-bg)] ring-offset-2 ring-offset-[var(--surface)]",
] as const;

export const TIER_NAMES = ["Níveis 1 a 3", "Níveis 4 a 6", "Níveis 7 e 8", "Níveis 9 e 10"] as const;

export function tierOf(level: number): number {
  if (level <= 3) return 0;
  if (level <= 6) return 1;
  if (level <= 8) return 2;
  return 3;
}

export function LevelBadge({ level, size = "md", className }: { level: number | null; size?: "xs" | "sm" | "md" | "lg"; className?: string }) {
  if (level === null) return null;
  const tier = tierOf(level);
  return (
    <span
      className={clsx(
        "num inline-flex shrink-0 items-center justify-center leading-none",
        // A forma cresce com a faixa: quadrado, quadrado chanfrado, losango suave e escudo com anel.
        tier === 0 && "rounded-md",
        tier === 1 && "rounded-lg",
        tier >= 2 && "rounded-xl",
        size === "lg" ? "size-10 text-2xl" : size === "md" ? "size-8 text-xl" : size === "sm" ? "size-6 text-base" : "size-[1.15rem] text-xs",
        LEVEL_TIERS[tier],
        className,
      )}
    >
      <span className="sr-only">Nível </span>
      {level}
    </span>
  );
}

/** Legenda das faixas de nível, para quem vê o selo e quer saber o que a cor significa. */
export function LevelLegend({ className }: { className?: string }) {
  return (
    <ul className={clsx("flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-muted", className)} aria-label="Faixas de nível">
      {[1, 4, 7, 9].map((level, tier) => (
        <li key={level} className="inline-flex items-center gap-2">
          <span aria-hidden="true" className={clsx("num inline-flex size-6 items-center justify-center rounded-md text-base leading-none", tier === 3 ? "rounded-lg" : "", LEVEL_TIERS[tier])}>
            {level === 9 ? "9+" : level}
          </span>
          {TIER_NAMES[tier]}
        </li>
      ))}
    </ul>
  );
}

/** Forma V/D: letra e cor, nunca só cor. Mais recente primeiro. */
export type FormItem = { result: "win" | "loss" | "unknown"; map?: string; detail?: string };

export function FormStrip({ items, label }: { items: FormItem[]; label: string }) {
  if (items.length === 0) return null;
  return (
    <ul role="img" aria-label={label} className="flex flex-wrap gap-2">
      {items.map((item, i) => (
        <li
          key={i}
          aria-hidden="true"
          title={[item.map, item.detail].filter(Boolean).join(" · ") || undefined}
          className={clsx(
            "flex w-16 flex-col items-center rounded-lg border px-1 py-1 text-center leading-none",
            item.result === "win" && "border-win/40 bg-win-bg text-win",
            item.result === "loss" && "border-loss/40 bg-loss-bg text-loss",
            item.result === "unknown" && "border-line-soft bg-surface-3 text-muted",
          )}
        >
          <span className="num text-2xl">{item.result === "win" ? "V" : item.result === "loss" ? "D" : "–"}</span>
          {item.map && <span className="mt-1 w-full truncate text-[0.7rem] font-semibold text-muted">{item.map}</span>}
        </li>
      ))}
    </ul>
  );
}
