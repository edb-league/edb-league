import clsx from "clsx";
import Link from "next/link";
import { Progress } from "@/components/ui/Charts";
import { seasonQuery, seasonSummary } from "@/lib/format";
import type { Meta } from "@/lib/types";

/** Barra da temporada: situação (texto + progresso) e links para trocar de temporada. */
export function SeasonBar({
  meta,
  season,
  path,
  extra,
  variant = "card",
}: {
  meta: Meta;
  season: number;
  path: string;
  /** Parâmetros preservados ao trocar de temporada. */
  extra?: Record<string, string | undefined>;
  /** "strip" não desenha moldura própria: vai dentro do banner da página. */
  variant?: "card" | "strip";
}) {
  const current = meta.seasons.find((s) => s.number === season);
  if (!current) return null;
  const numbers = meta.seasons.map((s) => s.number).filter((n) => n >= 1);
  const latest = Math.max(...numbers, 1);
  const visible = new Set<number>([season, latest]);
  for (const n of numbers) if (Math.abs(n - season) <= 2) visible.add(n);
  const options = meta.seasons.filter((s) => visible.has(s.number)).sort((a, b) => b.number - a.number);

  return (
    <section
      aria-label="Temporada"
      className={clsx(
        "flex flex-wrap items-center justify-between gap-x-4 gap-y-2",
        variant === "card" && "rounded-[var(--radius-card)] border border-line-soft bg-surface px-4 py-3",
      )}
    >
      <div className="min-w-0 flex-1 basis-64">
        <p className="flex flex-wrap items-baseline gap-x-3">
          <span className="font-display text-2xl font-bold uppercase">{current.label}</span>
          <span className="text-base text-muted">{seasonSummary(current)}</span>
        </p>
        {current.status === "active" && current.progress && (
          <div className="mt-1 max-w-xs">
            <Progress
              value={(100 * current.progress.day) / current.progress.total_days}
              label={`Dia ${current.progress.day} de ${current.progress.total_days}`}
            />
          </div>
        )}
      </div>
      {options.length > 1 && (
        <nav aria-label="Selecionar temporada">
          <ul className="flex flex-wrap gap-2">
            {options.map((s) => {
              const active = s.number === season;
              return (
                <li key={s.number}>
                  <Link
                    href={`${path}${seasonQuery(s.number, extra)}`}
                    aria-current={active ? "page" : undefined}
                    className={clsx(
                      "press lift inline-flex min-h-11 items-center rounded-lg border px-4 text-base font-bold no-underline",
                      active
                        ? "border-gold-bg bg-gold-bg text-on-gold"
                        : "border-line bg-surface-2 text-fg hover:bg-surface-3",
                    )}
                  >
                    {s.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
      )}
    </section>
  );
}
