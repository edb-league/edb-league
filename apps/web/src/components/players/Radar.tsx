import type { StyleItem } from "@/components/players/StyleBars";

const CX = 190;
const CY = 150;
const R = 100;

/**
 * Radar das notas 0 a 100 (posição entre os jogadores da liga). O anel tracejado em azul é o meio da
 * liga (50): quem passa dele está acima da média nessa nota. Os números também estão em texto, logo
 * abaixo, então o desenho é um reforço visual.
 */
export function Radar({ items }: { items: StyleItem[] }) {
  const n = items.length;
  if (n < 3) return null;
  const point = (i: number, radius: number) => {
    const angle = ((-90 + (i * 360) / n) * Math.PI) / 180;
    return [CX + radius * Math.cos(angle), CY + radius * Math.sin(angle)] as const;
  };
  const ring = (fraction: number) =>
    items.map((_, i) => point(i, R * fraction).map((v) => v.toFixed(1)).join(",")).join(" ");
  const shape = items.map((item, i) => point(i, (R * (item.score ?? 0)) / 100).map((v) => v.toFixed(1)).join(",")).join(" ");
  const summary = `Radar das notas: ${items.map((i) => `${i.label} ${i.score ?? "sem dado"}`).join(", ")}.`;

  return (
    <svg viewBox="0 0 380 300" role="img" aria-label={summary} className="mx-auto h-auto w-full max-w-md">
      {[0.25, 0.75, 1].map((f) => (
        <polygon key={f} points={ring(f)} fill="none" stroke="var(--border-soft)" strokeWidth="1" />
      ))}
      <polygon points={ring(0.5)} fill="none" stroke="var(--accent)" strokeWidth="1.5" strokeDasharray="5 4" />
      {items.map((_, i) => {
        const [x, y] = point(i, R);
        return <line key={i} x1={CX} y1={CY} x2={x} y2={y} stroke="var(--border-soft)" strokeWidth="1" />;
      })}
      <polygon points={shape} fill="var(--gold-bg)" fillOpacity="0.28" stroke="var(--gold-bg)" strokeWidth="2.5" strokeLinejoin="round" />
      {items.map((item, i) => {
        const [x, y] = point(i, (R * (item.score ?? 0)) / 100);
        const [lx, ly] = point(i, R + 18);
        const anchor = lx < CX - 8 ? "end" : lx > CX + 8 ? "start" : "middle";
        return (
          <g key={item.label}>
            <circle cx={x} cy={y} r="4" fill="var(--gold-bg)" stroke="var(--surface)" strokeWidth="2" />
            <text x={lx} y={ly + 4} textAnchor={anchor} fontSize="13" fontWeight="700" fill="var(--text)">
              {item.label}
              <tspan x={lx} dy="14" fontSize="12" fontWeight="500" fill="var(--text-muted)">
                {item.score ?? "–"}
              </tspan>
            </text>
          </g>
        );
      })}
    </svg>
  );
}
