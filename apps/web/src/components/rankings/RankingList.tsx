import clsx from "clsx";
import Link from "next/link";
import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/Card";
import { num } from "@/lib/format";
import type { Ranking, RankingRow } from "@/lib/types";

function Stars({ count }: { count: number }) {
  if (count <= 0) return null;
  return (
    <span role="img" aria-label={`${count} ${count === 1 ? "estrela" : "estrelas"}`} className="text-base text-gold">
      {"★".repeat(count)}
    </span>
  );
}

function secondary(row: RankingRow, type: Ranking["type"]): string {
  if (type === "bagres") return "Ordenado por menor ADR acumulado nos mapas disputados";
  const parts: string[] = [];
  if (type !== "elite") parts.push(`Índice Elite: ${num(row.elite, 1)}`);
  if (type !== "superacao") parts.push(`Superação: ${num(row.superacao, 1, "%")}`);
  if (type !== "xp") parts.push(`XP: ${num(row.xp)}`);
  return parts.join(" · ");
}

/**
 * Classificação em cartões. O nome do jogador é o link; ele se estende sobre o cartão
 * inteiro (padrão "stretched link"), então há um único alvo de foco por jogador.
 */
export function RankingList({ ranking }: { ranking: Ranking }) {
  if (ranking.rows.length === 0) {
    return <EmptyState>Ainda não há partidas registradas nesse período.</EmptyState>;
  }
  const decimals = ranking.type === "xp" ? 0 : 1;
  return (
    <ol className="flex flex-col gap-3" aria-label={ranking.title}>
      {ranking.rows.map((row) => {
        const metrics: [string, string][] = [
          ["Partidas", num(row.matches)],
          ["Kills", num(row.kills)],
          ["K/D", num(row.kd, 2)],
          ["KPR", num(row.kpr, 3)],
          ["ADR", num(row.adr, 1)],
          ["Vitórias", num(row.wins)],
        ];
        return (
          <li
            key={row.player_id}
            className={clsx(
              "card group relative p-4 hover:bg-surface-2 md:p-5",
              row.rank === 1 && "border-l-4 border-l-gold",
            )}
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex min-w-0 items-start gap-3">
                <span className="tabular min-w-9 pt-0.5 text-base font-bold text-muted">
                  <span className="sr-only">Posição </span>#{String(row.rank).padStart(2, "0")}
                </span>
                <div className="min-w-0">
                  <h3 className="text-lg font-bold break-words">
                    <Link
                      href={`/jogadores/${encodeURIComponent(row.player_id)}`}
                      className="text-fg no-underline group-hover:underline after:absolute after:inset-0 after:content-['']"
                    >
                      {row.name}
                    </Link>
                  </h3>
                  <p className="text-base text-muted">
                    {ranking.type === "bagres" ? (
                      row.level !== null ? `Nível ${row.level}` : "Sem nível"
                    ) : (
                      <Stars count={row.stars} />
                    )}
                  </p>
                </div>
              </div>
              <div className="shrink-0 text-right">
                <p className="text-sm text-muted">{ranking.focus_label}</p>
                <p className="tabular text-2xl font-extrabold text-gold">
                  {num(row.focus, decimals, ranking.focus_unit)}
                </p>
              </div>
            </div>

            <dl className="mt-4 grid grid-cols-3 gap-x-3 gap-y-3 border-t border-line-soft pt-4 md:grid-cols-6">
              {metrics.map(([label, value]) => (
                <div key={label}>
                  <dt className="text-sm text-muted">{label}</dt>
                  <dd className="tabular text-base font-bold">{value}</dd>
                </div>
              ))}
            </dl>

            <p className="mt-3 flex flex-wrap items-center gap-2 text-sm text-muted">
              <span>{secondary(row, ranking.type)}</span>
              {row.provisional && (
                <Badge tone="gold">
                  Provisório ({ranking.type === "bagres" ? "menos de 2 mapas" : "menos de 6 mapas"})
                </Badge>
              )}
            </p>
          </li>
        );
      })}
    </ol>
  );
}
