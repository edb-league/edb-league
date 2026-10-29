import clsx from "clsx";
import Link from "next/link";
import { num } from "@/lib/format";

/* ---------- Barras horizontais em HTML (lista ordenada) ---------- */

export type BarItem = { id: string; label: string; value: number; display?: string; href?: string };

/**
 * Ranking em barras. É uma lista <ol>: o leitor de tela lê "nome, valor" em cada item;
 * a barra é apenas reforço visual. Não depende de SVG nem de bibliotecas.
 */
export function BarList({
  items,
  tone = "gold",
  caption,
  decimals = 1,
}: {
  items: BarItem[];
  tone?: "gold" | "accent";
  caption: string;
  decimals?: number;
}) {
  const max = Math.max(...items.map((i) => i.value), 1);
  return (
    <figure>
      <figcaption className="sr-only">{caption}</figcaption>
      <ol className="flex flex-col gap-2">
        {items.map((item, index) => (
          <li key={item.id} className="grid grid-cols-[1.75rem_minmax(0,9rem)_1fr_auto] items-center gap-2 sm:grid-cols-[2rem_minmax(0,12rem)_1fr_auto] sm:gap-3">
            <span className="tabular text-sm text-muted">{index + 1}.</span>
            {item.href ? (
              <Link href={item.href} className="truncate text-base font-bold" title={item.label}>
                {item.label}
              </Link>
            ) : (
              <span className="truncate text-base font-bold" title={item.label}>
                {item.label}
              </span>
            )}
            <span aria-hidden="true" className="h-3.5 overflow-hidden rounded-full bg-surface-3">
              <span
                className={clsx("block h-full rounded-full", tone === "gold" ? "bg-gold" : "bg-accent-bg")}
                style={{ width: `${Math.max(2, (item.value / max) * 100)}%` }}
              />
            </span>
            <span className="tabular min-w-12 text-right text-base font-bold">
              {item.display ?? num(item.value, decimals)}
            </span>
          </li>
        ))}
      </ol>
    </figure>
  );
}

/* ---------- Pares de barras (comparação de dois jogadores por mapa) ---------- */

export type PairItem = { id: string; label: string; a: number; b: number };

export function PairBars({
  items,
  nameA,
  nameB,
  unit,
  caption,
}: {
  items: PairItem[];
  nameA: string;
  nameB: string;
  unit: string;
  caption: string;
}) {
  const max = Math.max(...items.flatMap((i) => [i.a, i.b]), 1);
  return (
    <figure>
      <figcaption className="sr-only">{caption}</figcaption>
      <p className="mb-3 flex flex-wrap gap-x-5 gap-y-1 text-sm text-muted" aria-hidden="true">
        <span>
          <span className="mr-1.5 inline-block size-3 rounded-sm bg-accent-bg align-middle" />
          {nameA}
        </span>
        <span>
          <span className="mr-1.5 inline-block size-3 rounded-sm bg-pt align-middle" />
          {nameB}
        </span>
      </p>
      <ul className="flex flex-col gap-4">
        {items.map((item) => (
          <li key={item.id}>
            <p className="mb-1 text-base font-bold">{item.label}</p>
            {(
              [
                [nameA, item.a, "bg-accent-bg"],
                [nameB, item.b, "bg-pt"],
              ] as const
            ).map(([name, value, color]) => (
              <div key={name} className="mb-1 grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3">
                <span className="h-3.5 overflow-hidden rounded-full bg-surface-3" aria-hidden="true">
                  <span className={clsx("block h-full rounded-full", color)} style={{ width: `${Math.max(2, (value / max) * 100)}%` }} />
                </span>
                <span className="tabular min-w-24 text-right text-base">
                  <span className="sr-only">{name}: </span>
                  <b>{num(value)}</b> {unit}
                </span>
              </div>
            ))}
          </li>
        ))}
      </ul>
    </figure>
  );
}

/* ---------- Barra de progresso ---------- */

export function Progress({ value, label, tone = "accent" }: { value: number; label: string; tone?: "accent" | "gold" }) {
  const v = Math.max(0, Math.min(100, value));
  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={Math.round(v)}
      className="h-2.5 overflow-hidden rounded-full bg-surface-3"
    >
      <div className={clsx("progress-fill h-full rounded-full", tone === "gold" ? "bg-gold-bg" : "bg-accent-bg")} style={{ width: `${v}%` }} />
    </div>
  );
}
