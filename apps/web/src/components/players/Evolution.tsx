"use client";

import { useMemo, useState } from "react";
import { LineChart } from "@/components/ui/LineChart";
import { dayMonth } from "@/lib/format";
import type { PlayerMatchRow } from "@/lib/types";

const METRICS = {
  kd: { label: "K/D", decimals: 2 },
  adr: { label: "ADR", decimals: 1 },
  kpr: { label: "KPR", decimals: 3 },
  kills: { label: "Kills", decimals: 0 },
} as const;

type MetricKey = keyof typeof METRICS;

/** Evolução por partida, da mais antiga para a mais recente. A métrica troca por abas. */
export function Evolution({
  matches,
  averages,
}: {
  matches: PlayerMatchRow[];
  /** Média da liga por métrica, quando existe. */
  averages?: Partial<Record<MetricKey, number | null>>;
}) {
  const [metric, setMetric] = useState<MetricKey>("kd");

  const points = useMemo(
    () =>
      [...matches].reverse().map((m) => ({
        label: `${dayMonth(m.date)} · ${m.map}`,
        short: dayMonth(m.date),
        value: m[metric],
      })),
    [matches, metric],
  );

  return (
    <div className="flex flex-col gap-4">
      <div role="group" aria-label="Métrica do gráfico" className="flex flex-wrap gap-2">
        {(Object.keys(METRICS) as MetricKey[]).map((key) => (
          <button
            key={key}
            type="button"
            aria-pressed={metric === key}
            onClick={() => setMetric(key)}
            className={`press lift min-h-11 rounded-lg border px-4 text-base font-bold ${
              metric === key ? "border-gold-bg bg-gold-bg text-on-gold" : "border-line bg-surface text-fg hover:bg-surface-2"
            }`}
          >
            {METRICS[key].label}
          </button>
        ))}
      </div>
      <LineChart points={points} metric={METRICS[metric].label} decimals={METRICS[metric].decimals} average={averages?.[metric] ?? null} />
    </div>
  );
}
