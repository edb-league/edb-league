import clsx from "clsx";
import Link from "next/link";
import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/Card";
import { LevelBadge } from "@/components/ui/LevelBadge";
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
 * Classificação em cartões, em duas colunas no computador. O nome do jogador é o link;
 * ele se estende sobre o cartão inteiro (padrão "stretched link"), então há um único
 * alvo de foco por jogador.
 */
export function RankingList({ ranking }: { ranking: Ranking }) {
  if (ranking.rows.length === 0) {
    return <EmptyState>Ainda não há partidas registradas nesse período.</EmptyState>;
  }
  const decimals = ranking.type === "xp" ? 0 : 1;
  return (
    <ol className="grid gap-3 lg:grid-cols-2" aria-label={ranking.title}>
      {ranking.rows.map((row) => {
        const metrics: [string, string][] = [
          // O ranking conta só os melhores mapas de cada jogador (Regulamento): "6 de 12".
          ["Mapas", row.maps_played != null && row.maps_played !== row.matches
            ? `${num(row.matches)} de ${num(row.maps_played)}`
            : num(row.matches)],
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
              "card group relative p-3 hover:bg-surface-2 md:p-4",
              row.rank === 1 && "border-l-4 border-l-gold-bg",
            )}
          >
            <div className="flex items-center justify-between gap-3">
              <div className="flex min-w-0 items-center gap-3">
                <span className="num min-w-10 text-3xl leading-none text-muted">
                  <span className="sr-only">Posição </span>#{String(row.rank).padStart(2, "0")}
                </span>
                <div className="min-w-0">
                  <h3 className="flex flex-wrap items-center gap-x-2 text-xl leading-tight font-bold break-words">
                    {ranking.type !== "bagres" && <LevelBadge level={row.level} />}
                    <Link
                      href={`/jogadores/${encodeURIComponent(row.player_id)}`}
                      className="text-fg no-underline group-hover:underline after:absolute after:inset-0 after:content-['']"
                    >
                      {row.name}
                    </Link>
                  </h3>
                  <p className="text-base leading-tight text-muted">
                    {ranking.type === "bagres" ? (
                      row.level !== null ? `Nível ${row.level}` : "Sem nível"
                    ) : (
                      <Stars count={row.stars} />
                    )}
                  </p>
                </div>
              </div>
              <div className="shrink-0 text-right">
                <p className="text-sm leading-tight text-muted">{ranking.focus_label}</p>
                <p className="num text-3xl leading-none text-gold md:text-4xl">
                  {num(row.focus, decimals, ranking.focus_unit)}
                </p>
              </div>
            </div>

            <dl className="mt-3 grid grid-cols-3 gap-x-3 gap-y-2 border-t border-line-soft pt-3 sm:grid-cols-6">
              {metrics.map(([label, value]) => (
                <div key={label}>
                  <dt className="text-sm leading-tight text-muted">{label}</dt>
                  <dd className="tabular text-base leading-tight font-bold">{value}</dd>
                </div>
              ))}
            </dl>

            <p className="mt-2 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-muted">
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
