"use client";

import { useId, useMemo, useState } from "react";
import { LineChart } from "@/components/ui/Charts";
import { controlClass } from "@/components/ui/Field";
import { dayMonth } from "@/lib/format";
import type { PlayerMatchRow } from "@/lib/types";

const METRICS = {
  kd: { label: "K/D", decimals: 2 },
  adr: { label: "ADR", decimals: 1 },
  kpr: { label: "KPR", decimals: 3 },
  kills: { label: "Kills", decimals: 0 },
} as const;

type MetricKey = keyof typeof METRICS;

/** Evolução por partida, da mais antiga para a mais recente, com métrica escolhida pelo usuário. */
export function Evolution({ matches }: { matches: PlayerMatchRow[] }) {
  const id = useId();
  const [metric, setMetric] = useState<MetricKey>("kd");

  const points = useMemo(
    () =>
      [...matches].reverse().map((m) => ({
        label: `${dayMonth(m.date)} ${m.map}`,
        value: m[metric],
      })),
    [matches, metric],
  );

  return (
    <div className="flex flex-col gap-4">
      <div className="flex max-w-xs flex-col gap-1.5">
        <label htmlFor={id} className="text-base font-bold">
          Métrica
        </label>
        <select id={id} className={controlClass} value={metric} onChange={(e) => setMetric(e.target.value as MetricKey)}>
          {Object.entries(METRICS).map(([key, m]) => (
            <option key={key} value={key}>
              {m.label}
            </option>
          ))}
        </select>
      </div>
      <LineChart points={points} metric={METRICS[metric].label} decimals={METRICS[metric].decimals} />
    </div>
  );
}
