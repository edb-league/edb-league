import clsx from "clsx";
import { SectionTitle } from "@/components/ui/Card";
import type { MapCard, RoundEntry, RoundReason, RoundTimeline as Timeline } from "@/lib/types";

const REASON: Record<RoundReason, { letter: string; label: string }> = {
  eliminacao: { letter: "E", label: "eliminação do time inimigo" },
  bomba: { letter: "B", label: "bomba explodiu" },
  desarme: { letter: "D", label: "bomba desarmada" },
  tempo: { letter: "T", label: "tempo esgotado" },
};

const SIDE = { t: "T", ct: "CT" } as const;

function describe(round: RoundEntry, left: string, right: string): string {
  const winner = round.winner === "left" ? left : right;
  const why = round.reason ? REASON[round.reason].label : "motivo não informado pela demo";
  const bomb = round.planted && round.reason !== "bomba" && round.reason !== "desarme" ? ", bomba plantada" : "";
  return `Round ${round.round}: ${winner} (${SIDE[round.side]}) venceu por ${why}${bomb}. Placar ${round.score_left} a ${round.score_right}.`;
}

/** Cada round como uma coluna; o time que venceu marca a própria linha. Cor nunca é o único sinal: há letra e texto. */
export function RoundTimeline({ timeline, match }: { timeline: Timeline; match: MapCard }) {
  const { rounds } = timeline;
  const last = rounds[rounds.length - 1];
  const rows = [
    { side: "left" as const, name: match.left, tone: "border-pt text-pt" },
    { side: "right" as const, name: match.right, tone: "border-pl text-pl" },
  ];
  const legend = Object.values(REASON);
  return (
    <section aria-labelledby="linha-rounds">
      <SectionTitle id="linha-rounds" title="Linha do tempo dos rounds">
        Quem venceu cada round e como. A marcação grossa separa os lados do intervalo (depois do round 12).
      </SectionTitle>
      <div className="card p-4 md:p-6">
        <p className="mb-3 text-base text-muted">
          {legend.map((l, i) => (
            <span key={l.letter}>
              {i > 0 && " · "}
              <b className="text-fg">{l.letter}</b> {l.label}
            </span>
          ))}
        </p>
        <div role="region" aria-label="Linha do tempo dos rounds (role para o lado)" tabIndex={0} className="overflow-x-auto rounded-lg">
          <div aria-hidden="true" className="grid w-max gap-y-1.5 text-center" style={{ gridTemplateColumns: `6rem repeat(${rounds.length}, 2.25rem)` }}>
            <span />
            {rounds.map((r) => (
              <span key={r.round} className={clsx("num text-sm text-muted", r.round === 13 && "border-l-4 border-line")}>
                {r.round}
              </span>
            ))}
            {rows.map((row) => (
              <div key={row.side} className="contents">
                <span className="truncate pr-2 text-right text-lg font-bold">{row.name}</span>
                {rounds.map((r) => (
                  <span key={r.round} className={clsx("flex h-9 items-center justify-center", r.round === 13 && "border-l-4 border-line")}>
                    {r.winner === row.side && (
                      <span
                        title={describe(r, match.left, match.right)}
                        className={clsx("num flex size-8 items-center justify-center rounded-md border-2 bg-surface-2 text-lg leading-none", row.tone)}
                      >
                        {r.reason ? REASON[r.reason].letter : "·"}
                      </span>
                    )}
                  </span>
                ))}
              </div>
            ))}
          </div>
        </div>
        <ol className="sr-only" aria-label="Resultado de cada round">
          {rounds.map((r) => (
            <li key={r.round}>{describe(r, match.left, match.right)}</li>
          ))}
        </ol>
        {last && (
          <p className="mt-3 text-base text-muted">
            Placar final: {match.left} <b className="num text-fg">{last.score_left}</b> × <b className="num text-fg">{last.score_right}</b> {match.right}
          </p>
        )}
      </div>
    </section>
  );
}
