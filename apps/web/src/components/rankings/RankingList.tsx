import clsx from "clsx";
import Link from "next/link";
import { Avatar } from "@/components/ui/Avatar";
import { Badge, YouBadge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/Card";
import { LevelBadge } from "@/components/ui/LevelBadge";
import { TableWrap, Td, Th } from "@/components/ui/Table";
import { num } from "@/lib/format";
import type { Ranking, RankingRow } from "@/lib/types";
import { StarRow } from "@/components/ui/Icon";

function Stars({ count }: { count: number }) {
  if (count <= 0) return null;
  return (
    <span role="img" aria-label={`${count} ${count === 1 ? "estrela" : "estrelas"}`} className="text-base text-gold">
      <StarRow count={count} />
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

/** Mapas contados no ranking: "6 de 12" quando o jogador tem mais mapas do que os 6 que entram. */
function mapsLabel(row: RankingRow): string {
  return row.maps_played != null && row.maps_played !== row.matches
    ? `${num(row.matches)} de ${num(row.maps_played)}`
    : num(row.matches);
}

/** Quantos mapas ainda faltam para o jogador entrar na disputa oficial (6; 2 no BAGRES). */
function missingMaps(row: RankingRow, type: Ranking["type"]): number {
  const need = type === "bagres" ? 2 : 6;
  return Math.max(need - (row.maps_played ?? row.matches), 0);
}

function ProvisionalBadge({ row, type }: { row: RankingRow; type: Ranking["type"] }) {
  const missing = missingMaps(row, type);
  return (
    <Badge tone="gold">
      Provisório{missing > 0 ? ` · faltam ${missing} ${missing === 1 ? "mapa" : "mapas"}` : ""}
    </Badge>
  );
}

function PlayerLink({ row, stretched }: { row: RankingRow; stretched?: boolean }) {
  return (
    <Link
      href={`/jogadores/${encodeURIComponent(row.player_id)}`}
      className={clsx(
        "text-fg no-underline group-hover:underline hover:underline",
        stretched && "after:absolute after:inset-0 after:content-['']",
      )}
    >
      {row.name}
    </Link>
  );
}

/** Cartão do pódio (três primeiros): o líder em ouro e maior, os outros dois em azul. */
function PodiumCard({ row, ranking, avatar, mine }: { row: RankingRow; ranking: Ranking; avatar?: string; mine: boolean }) {
  const first = row.rank === 1;
  const decimals = ranking.type === "xp" ? 0 : 1;
  return (
    <li
      className={clsx(
        "card group relative flex flex-col gap-3 p-4 card-press hover:bg-surface-2",
        first ? "border-2 border-gold-bg bg-surface-2 md:p-6" : "md:mt-6 md:p-5",
        mine && "ring-2 ring-accent ring-offset-2 ring-offset-bg",
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <span className={clsx("num leading-none", first ? "text-6xl text-gold" : "text-5xl text-muted")}>
          <span className="sr-only">Posição </span>
          {row.rank}º
        </span>
        <div className="text-right">
          <p className="text-sm leading-tight text-muted">{ranking.focus_label}</p>
          <p className={clsx("num leading-none", first ? "text-5xl text-gold" : "text-4xl")}>
            {num(row.focus, decimals, ranking.focus_unit)}
          </p>
        </div>
      </div>
      <div className="flex min-w-0 items-center gap-3">
        <Avatar
          name={row.name}
          src={avatar}
          size={first ? 64 : 56}
          level={ranking.type === "bagres" ? null : row.level}
          decorative
          className="border-2"
        />
        <div className="min-w-0">
          <h3 className="flex flex-wrap items-center gap-x-2 text-2xl leading-tight font-bold break-words">
            <PlayerLink row={row} stretched />
            {mine && <YouBadge />}
          </h3>
          <p className="mt-0.5 text-base text-muted">
            {ranking.type === "bagres" ? (row.level !== null ? `Nível ${row.level}` : "Sem nível") : <Stars count={row.stars} />}
          </p>
        </div>
      </div>
      <dl className="grid grid-cols-4 gap-2 border-t border-line-soft pt-3">
        {(
          [
            ["K/D", num(row.kd, 2)],
            ["KPR", num(row.kpr, 3)],
            ["ADR", num(row.adr, 1)],
            ["Mapas", mapsLabel(row)],
          ] as const
        ).map(([label, value]) => (
          <div key={label}>
            <dt className="text-sm leading-tight text-muted">{label}</dt>
            <dd className="tabular text-lg leading-tight font-bold">{value}</dd>
          </div>
        ))}
      </dl>
    </li>
  );
}

/** Cartão compacto para telas estreitas, onde a tabela não cabe. */
function RowCard({ row, ranking, mine }: { row: RankingRow; ranking: Ranking; mine: boolean }) {
  const decimals = ranking.type === "xp" ? 0 : 1;
  const metrics: [string, string][] = [
    ["Mapas", mapsLabel(row)],
    ["Kills", num(row.kills)],
    ["K/D", num(row.kd, 2)],
    ["KPR", num(row.kpr, 3)],
    ["ADR", num(row.adr, 1)],
    ["Vitórias", num(row.wins)],
  ];
  return (
    <li className={clsx("card group relative p-3 card-press hover:bg-surface-2", row.rank === 1 && "border-gold-bg", mine && "ring-2 ring-accent")}>
      <div className="flex items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-3">
          <span className="num min-w-10 text-3xl leading-none text-muted">
            <span className="sr-only">Posição </span>#{String(row.rank).padStart(2, "0")}
          </span>
          <div className="min-w-0">
            <h3 className="flex flex-wrap items-center gap-x-2 text-xl leading-tight font-bold break-words">
              {ranking.type !== "bagres" && <LevelBadge level={row.level} />}
              <PlayerLink row={row} stretched />
              {mine && <YouBadge />}
            </h3>
            <p className="text-base leading-tight text-muted">
              {ranking.type === "bagres" ? (row.level !== null ? `Nível ${row.level}` : "Sem nível") : <Stars count={row.stars} />}
            </p>
          </div>
        </div>
        <div className="shrink-0 text-right">
          <p className="text-sm leading-tight text-muted">{ranking.focus_label}</p>
          <p className={clsx("num text-3xl leading-none", row.rank === 1 && "text-gold")}>
            {num(row.focus, decimals, ranking.focus_unit)}
          </p>
        </div>
      </div>
      <dl className="mt-3 grid grid-cols-3 gap-x-3 gap-y-2 border-t border-line-soft pt-3">
        {metrics.map(([label, value]) => (
          <div key={label}>
            <dt className="text-sm leading-tight text-muted">{label}</dt>
            <dd className="tabular text-base leading-tight font-bold">{value}</dd>
          </div>
        ))}
      </dl>
      <p className="mt-2 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-muted">
        <span>{secondary(row, ranking.type)}</span>
        {row.provisional && <ProvisionalBadge row={row} type={ranking.type} />}
      </p>
    </li>
  );
}

/** Tabela de leitura rápida: colunas alinhadas para comparar jogadores lado a lado. */
function RankingTable({
  rows,
  ranking,
  caption,
  avatars,
  meId,
}: {
  rows: RankingRow[];
  ranking: Ranking;
  caption: string;
  avatars: Record<string, string>;
  meId?: string;
}) {
  const decimals = ranking.type === "xp" ? 0 : 1;
  return (
    <TableWrap caption={caption}>
      <thead>
        <tr>
          <Th numeric>Pos.</Th>
          <Th>Jogador</Th>
          <Th numeric>{ranking.focus_label}</Th>
          <Th numeric>Mapas</Th>
          <Th numeric>Kills</Th>
          <Th numeric>K/D</Th>
          <Th numeric>KPR</Th>
          <Th numeric>ADR</Th>
          <Th numeric>Vitórias</Th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr
            key={row.player_id}
            className={clsx("transition-colors duration-150 hover:bg-surface-2", row.player_id === meId && "bg-surface-2 outline-2 -outline-offset-2 outline-accent")}
          >
            <Td numeric className="num w-16 text-2xl text-muted">
              {row.rank}
            </Td>
            <Td>
              <span className="flex flex-wrap items-center gap-x-2 gap-y-1">
                {ranking.type !== "bagres" && <LevelBadge level={row.level} />}
                <Avatar name={row.name} src={avatars[row.player_id]} size={30} decorative className="border-2" />
                <span className="text-lg font-bold">
                  <PlayerLink row={row} />
                </span>
                {ranking.type !== "bagres" && <Stars count={row.stars} />}
                {row.player_id === meId && <YouBadge />}
                {row.provisional && <ProvisionalBadge row={row} type={ranking.type} />}
              </span>
            </Td>
            <Td numeric className="num text-2xl">
              {num(row.focus, decimals, ranking.focus_unit)}
            </Td>
            <Td numeric>{mapsLabel(row)}</Td>
            <Td numeric>{num(row.kills)}</Td>
            <Td numeric>{num(row.kd, 2)}</Td>
            <Td numeric>{num(row.kpr, 3)}</Td>
            <Td numeric>{num(row.adr, 1)}</Td>
            <Td numeric>{num(row.wins)}</Td>
          </tr>
        ))}
      </tbody>
    </TableWrap>
  );
}

/**
 * Classificação. No computador: pódio com os três primeiros elegíveis e tabela com o restante;
 * quem ainda não tem os mapas mínimos fica separado, num bloco próprio. No celular: cartões.
 * O nome do jogador é o link; nos cartões ele se estende sobre o cartão inteiro.
 */
export function RankingList({ ranking, avatars = {}, meId }: { ranking: Ranking; avatars?: Record<string, string>; meId?: string }) {
  if (ranking.rows.length === 0) {
    return <EmptyState>Ainda não há partidas registradas nesse período.</EmptyState>;
  }
  const official = ranking.rows.filter((r) => !r.provisional);
  const provisional = ranking.rows.filter((r) => r.provisional);
  const podium = official.slice(0, 3);
  const rest = official.slice(3);
  const minMaps = ranking.type === "bagres" ? 2 : 6;

  return (
    <div className="flex flex-col gap-6">
      {/* Telas estreitas: todos em cartões, na ordem do ranking. */}
      <ol className="grid gap-3 md:hidden" aria-label={ranking.title}>
        {ranking.rows.map((row) => (
          <RowCard key={row.player_id} row={row} ranking={ranking} mine={row.player_id === meId} />
        ))}
      </ol>

      <div className="hidden flex-col gap-6 md:flex">
        {podium.length > 0 && (
          <ol className="grid grid-cols-3 items-start gap-4" aria-label={`Pódio: ${ranking.title}`}>
            {podium.map((row) => (
              <PodiumCard key={row.player_id} row={row} ranking={ranking} avatar={avatars[row.player_id]} mine={row.player_id === meId} />
            ))}
          </ol>
        )}
        {rest.length > 0 && <RankingTable rows={rest} ranking={ranking} caption={`Demais colocados: ${ranking.title}`} avatars={avatars} meId={meId} />}
        {provisional.length > 0 && (
          <section aria-labelledby="provisorios" className="flex flex-col gap-2">
            <h3 id="provisorios" className="text-xl font-bold">
              Ainda sem os {minMaps} mapas
            </h3>
            <p className="text-base text-muted">
              Estes jogadores aparecem com os números atuais, mas só entram na disputa oficial e nos títulos ao completar{" "}
              {minMaps} mapas na temporada.
            </p>
            <RankingTable rows={provisional} ranking={ranking} caption={`Provisórios: ${ranking.title}`} avatars={avatars} meId={meId} />
          </section>
        )}
      </div>
    </div>
  );
}
