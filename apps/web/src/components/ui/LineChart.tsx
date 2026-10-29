"use client";

import { useEffect, useId, useRef, useState } from "react";
import { num } from "@/lib/format";

export type LinePoint = { label: string; short: string; value: number | null };

/**
 * Gráfico de linha em SVG: linha dourada com área suave, média da liga tracejada em azul e dica ao
 * passar o mouse ou tocar. Vem com resumo textual e a tabela de valores logo abaixo.
 * Valores nulos interrompem a linha (nada é inventado).
 */
export function LineChart({
  points,
  metric,
  decimals = 2,
  average,
}: {
  points: LinePoint[];
  metric: string;
  decimals?: number;
  /** Média da liga para a mesma métrica, desenhada como referência. */
  average?: number | null;
}) {
  const uid = useId().replace(/:/g, "");
  const [active, setActive] = useState<number | null>(null);
  // O desenho usa a largura real da tela (1 unidade = 1 pixel), então o texto não encolhe no celular.
  const wrap = useRef<HTMLDivElement>(null);
  const [W, setW] = useState(640);
  useEffect(() => {
    const el = wrap.current;
    if (!el) return;
    const observer = new ResizeObserver(([entry]) => setW(Math.max(280, Math.round(entry?.contentRect.width ?? 640))));
    observer.observe(el);
    return () => observer.disconnect();
  }, []);
  const small = W < 480;
  const H = small ? 230 : 280;
  const M = { t: 18, r: 16, b: 34, l: small ? 38 : 48 };
  const valid = points.filter((p): p is LinePoint & { value: number } => p.value !== null);
  if (valid.length === 0) {
    return <p className="text-base text-muted">Ainda não há dados para esta métrica.</p>;
  }

  const values = valid.map((p) => p.value);
  if (average != null) values.push(average);
  const rawMin = Math.min(...values);
  const rawMax = Math.max(...values);
  const pad = (rawMax - rawMin) * 0.18 || Math.max(rawMax * 0.1, 0.5);
  const lo = Math.max(0, rawMin - pad);
  const hi = rawMax + pad;
  const x = (i: number) => M.l + (points.length === 1 ? (W - M.l - M.r) / 2 : (i / (points.length - 1)) * (W - M.l - M.r));
  const y = (v: number) => M.t + (1 - (v - lo) / (hi - lo)) * (H - M.t - M.b);
  const ticks = [0, 1 / 3, 2 / 3, 1].map((f) => lo + f * (hi - lo));
  const tickDecimals = decimals > 1 ? 1 : hi - lo < 4 ? 1 : 0;

  const segments: { i: number; v: number }[][] = [];
  let current: { i: number; v: number }[] = [];
  points.forEach((p, i) => {
    if (p.value === null) {
      if (current.length) segments.push(current);
      current = [];
    } else current.push({ i, v: p.value });
  });
  if (current.length) segments.push(current);
  const line = (seg: { i: number; v: number }[]) => seg.map((p) => `${x(p.i).toFixed(1)},${y(p.v).toFixed(1)}`).join(" ");
  const area = (seg: { i: number; v: number }[]) => {
    const first = seg[0]!;
    const last = seg[seg.length - 1]!;
    return `M${x(first.i).toFixed(1)},${(H - M.b).toFixed(1)} L${line(seg).replaceAll(" ", " L")} L${x(last.i).toFixed(1)},${(H - M.b).toFixed(1)} Z`;
  };

  const best = valid.reduce((a, b) => (b.value > a.value ? b : a));
  const bestIndex = points.indexOf(best);
  const summary = `${metric}: ${valid.length} partidas, de ${valid[0]!.label} a ${valid[valid.length - 1]!.label}. Melhor valor ${num(best.value, decimals)} em ${best.label}.${average != null ? ` Média da liga ${num(average, decimals)}.` : ""}`;
  const labelEvery = Math.max(1, Math.ceil(points.length / Math.max(2, Math.floor((W - M.l - M.r) / 62))));

  function nearest(clientX: number, rect: DOMRect) {
    const xv = ((clientX - rect.left) / rect.width) * W;
    let pick: number | null = null;
    let dist = Infinity;
    points.forEach((p, i) => {
      if (p.value === null) return;
      const d = Math.abs(x(i) - xv);
      if (d < dist) {
        dist = d;
        pick = i;
      }
    });
    return pick;
  }

  const tip = active !== null ? points[active] : null;

  return (
    <div>
      <div ref={wrap} className="relative mx-auto w-full max-w-3xl">
        <svg
          viewBox={`0 0 ${W} ${H}`}
          role="img"
          aria-label={summary}
          className="h-auto w-full touch-pan-y"
          onPointerMove={(e) => setActive(nearest(e.clientX, e.currentTarget.getBoundingClientRect()))}
          onPointerDown={(e) => setActive(nearest(e.clientX, e.currentTarget.getBoundingClientRect()))}
          onPointerLeave={() => setActive(null)}
        >
          <defs>
            <linearGradient id={`${uid}-area`} x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor="var(--gold-bg)" stopOpacity="0.32" />
              <stop offset="100%" stopColor="var(--gold-bg)" stopOpacity="0" />
            </linearGradient>
          </defs>
          {ticks.map((t) => (
            <g key={t}>
              <line x1={M.l} x2={W - M.r} y1={y(t)} y2={y(t)} stroke="var(--border-soft)" strokeWidth="1" />
              <text x={M.l - 8} y={y(t) + 4} textAnchor="end" fontSize="12" fill="var(--text-subtle)">
                {num(t, tickDecimals)}
              </text>
            </g>
          ))}
          {average != null && (
            <g>
              <line x1={M.l} x2={W - M.r} y1={y(average)} y2={y(average)} stroke="var(--accent)" strokeWidth="2" strokeDasharray="6 5" />
            </g>
          )}
          {segments.map((seg) => (
            <g key={seg[0]!.i}>
              {seg.length > 1 && <path d={area(seg)} fill={`url(#${uid}-area)`} />}
              <polyline points={line(seg)} fill="none" stroke="var(--gold-bg)" strokeWidth="3" strokeLinejoin="round" strokeLinecap="round" />
            </g>
          ))}
          {active !== null && tip?.value != null && (
            <line x1={x(active)} x2={x(active)} y1={M.t} y2={H - M.b} stroke="var(--border)" strokeWidth="1" strokeDasharray="3 4" />
          )}
          {points.map((p, i) =>
            p.value === null ? null : (
              <g key={`${p.label}-${i}`}>
                <circle
                  cx={x(i)}
                  cy={y(p.value)}
                  r={active === i ? 7 : i === bestIndex ? 6 : 4}
                  fill={i === bestIndex || active === i ? "var(--gold-bg)" : "var(--surface)"}
                  stroke="var(--gold-bg)"
                  strokeWidth="2.5"
                />
                {i % labelEvery === 0 && (
                  <text x={x(i)} y={H - 12} textAnchor="middle" fontSize="12" fill="var(--text-subtle)">
                    {p.short}
                  </text>
                )}
              </g>
            ),
          )}
        </svg>
        {tip && tip.value !== null && (
          <div
            aria-hidden="true"
            className="pointer-events-none absolute z-10 -translate-x-1/2 rounded-lg border border-line-soft bg-surface-2 px-3 py-1.5 text-center shadow-card"
            style={{
              left: `${Math.min(Math.max((x(active!) / W) * 100, 14), 86)}%`,
              top: `${(Math.max(y(tip.value) - 62, 0) / H) * 100}%`,
            }}
          >
            <p className="num text-2xl leading-none text-gold">{num(tip.value, decimals)}</p>
            <p className="mt-0.5 text-sm whitespace-nowrap text-muted">{tip.label}</p>
          </div>
        )}
      </div>
      <p className="mt-1 text-center text-sm text-muted">
        <span aria-hidden="true" className="mr-1.5 inline-block h-0.5 w-5 bg-gold-bg align-middle" />
        {metric} por partida
        {average != null && (
          <>
            <span aria-hidden="true" className="mr-1.5 ml-4 inline-block h-0 w-5 border-t-2 border-dashed border-accent align-middle" />
            Média da liga {num(average, decimals)}
          </>
        )}
      </p>
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
