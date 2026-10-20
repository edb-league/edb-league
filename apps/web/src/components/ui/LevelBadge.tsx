import clsx from "clsx";

/** Selo de nível (1 a 10). A faixa muda a cor, mas o número sempre aparece em texto. */
export const LEVEL_TIERS = [
  "bg-[var(--lv1-bg)] text-[var(--lv1-fg)]",
  "bg-[var(--lv2-bg)] text-[var(--lv2-fg)]",
  "bg-[var(--lv3-bg)] text-[var(--lv3-fg)]",
  "bg-[var(--lv4-bg)] text-[var(--lv4-fg)]",
] as const;

export function tierOf(level: number): number {
  if (level <= 3) return 0;
  if (level <= 6) return 1;
  if (level <= 8) return 2;
  return 3;
}

export function LevelBadge({ level, size = "md", className }: { level: number | null; size?: "md" | "lg"; className?: string }) {
  if (level === null) return null;
  return (
    <span
      className={clsx(
        "num inline-flex shrink-0 items-center justify-center rounded-lg leading-none",
        size === "lg" ? "size-9 text-2xl" : "size-8 text-xl",
        LEVEL_TIERS[tierOf(level)],
        className,
      )}
    >
      <span className="sr-only">Nível </span>
      {level}
    </span>
  );
}

/** Forma V/D: letra e cor, nunca só cor. Mais recente primeiro. */
export function FormStrip({ results, label }: { results: ("win" | "loss" | "unknown")[]; label: string }) {
  if (results.length === 0) return null;
  return (
    <span role="img" aria-label={label} className="inline-flex flex-wrap gap-1">
      {results.map((r, i) => (
        <span
          key={i}
          aria-hidden="true"
          className={clsx(
            "inline-flex size-6 items-center justify-center rounded-md text-sm font-bold",
            r === "win" && "bg-win-bg text-win",
            r === "loss" && "bg-loss-bg text-loss",
            r === "unknown" && "bg-surface-3 text-muted",
          )}
        >
          {r === "win" ? "V" : r === "loss" ? "D" : "–"}
        </span>
      ))}
    </span>
  );
}
