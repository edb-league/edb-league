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

/* ---------- Linha (evolução do jogador) ---------- */

export type LinePoint = { label: string; value: number | null };

/**
 * Gráfico de linha em SVG com resumo textual e tabela alternativa logo abaixo.
 * Valores nulos interrompem a linha (nada é inventado).
 */
export function LineChart({
  points,
  metric,
  decimals = 2,
}: {
  points: LinePoint[];
  metric: string;
  decimals?: number;
}) {
  const valid = points.filter((p): p is { label: string; value: number } => p.value !== null);
  if (valid.length === 0) {
    return <p className="text-base text-muted">Ainda não há dados para esta métrica.</p>;
  }
  const W = 640;
  const H = 260;
  const m = { t: 16, r: 16, b: 44, l: 48 };
  const max = Math.max(...valid.map((p) => p.value)) * 1.1 || 1;
  const x = (i: number) => m.l + (points.length === 1 ? (W - m.l - m.r) / 2 : (i / (points.length - 1)) * (W - m.l - m.r));
  const y = (v: number) => m.t + (1 - v / max) * (H - m.t - m.b);
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((f) => f * max);
  const segments: string[] = [];
  let current: string[] = [];
  points.forEach((p, i) => {
    if (p.value === null) {
      if (current.length) segments.push(current.join(" "));
      current = [];
    } else current.push(`${x(i).toFixed(1)},${y(p.value).toFixed(1)}`);
  });
  if (current.length) segments.push(current.join(" "));
  const best = valid.reduce((a, b) => (b.value > a.value ? b : a));
  const summary = `${metric}: ${valid.length} partidas, de ${valid[0]?.label} a ${valid[valid.length - 1]?.label}. Melhor valor ${num(best.value, decimals)} em ${best.label}.`;
  const labelEvery = Math.max(1, Math.ceil(points.length / 6));

  return (
    <div>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={summary} className="mx-auto h-auto w-full max-w-3xl">
        {ticks.map((t) => (
          <g key={t}>
            <line x1={m.l} x2={W - m.r} y1={y(t)} y2={y(t)} stroke="var(--border-soft)" strokeWidth="1" />
            <text x={m.l - 8} y={y(t) + 4} textAnchor="end" fontSize="12" fill="var(--text-subtle)">
              {num(t, decimals > 1 ? 1 : 0)}
            </text>
          </g>
        ))}
        {segments.map((s) => (
          <polyline key={s} points={s} fill="none" stroke="var(--accent)" strokeWidth="3" strokeLinejoin="round" />
        ))}
        {points.map((p, i) =>
          p.value === null ? null : (
            <g key={`${p.label}-${i}`}>
              <circle cx={x(i)} cy={y(p.value)} r="5" fill="var(--accent)" stroke="var(--surface)" strokeWidth="2">
                <title>{`${p.label}: ${num(p.value, decimals)}`}</title>
              </circle>
              {i % labelEvery === 0 && (
                <text x={x(i)} y={H - 16} textAnchor="middle" fontSize="12" fill="var(--text-subtle)">
                  {p.label}
                </text>
              )}
            </g>
          ),
        )}
      </svg>
      <details className="mt-2">
        <summary className="cursor-pointer text-base font-bold text-accent">Ver dados em tabela</summary>
        <div className="mt-2 overflow-x-auto" role="region" aria-label={`Dados de ${metric}`} tabIndex={0}>
          <table className="w-full text-base">
            <caption className="sr-only">{`Valores de ${metric} por partida`}</caption>
            <thead>
              <tr>
                <th scope="col" className="bg-surface-2 px-3 py-2 text-left text-sm text-muted">Partida</th>
                <th scope="col" className="bg-surface-2 px-3 py-2 text-right text-sm text-muted">{metric}</th>
              </tr>
            </thead>
            <tbody>
              {points.map((p, i) => (
                <tr key={`${p.label}-${i}`}>
                  <td className="border-t border-line-soft px-3 py-2">{p.label}</td>
                  <td className="tabular border-t border-line-soft px-3 py-2 text-right">{num(p.value, decimals)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
}

/* ---------- Barra de progresso ---------- */

export function Progress({ value, label }: { value: number; label: string }) {
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
      <div className="h-full rounded-full bg-accent-bg" style={{ width: `${v}%` }} />
    </div>
  );
}
