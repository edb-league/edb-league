import clsx from "clsx";
import Link from "next/link";
import { Badge, TeamTag } from "@/components/ui/Badge";
import type { MapCard, SeriesCard } from "@/lib/types";
import { NoData } from "@/components/ui/NoData";

function sideStatus(winner: "left" | "right" | null, side: "left" | "right") {
  if (winner === null) return { text: "Equipe", icon: "" };
  return winner === side ? { text: "Vencedor", icon: "✓" } : { text: "Derrotado", icon: "✕" };
}

function Score({ value, win, loss }: { value: number | null; win: boolean; loss: boolean }) {
  return (
    <span
      className={clsx(
        "tabular text-3xl font-extrabold",
        win && "text-win",
        loss && "text-loss",
      )}
    >
      {value ?? <NoData />}
    </span>
  );
}

function Side({
  name,
  status,
  asTag,
}: {
  name: string;
  status: { text: string; icon: string };
  asTag?: boolean;
}) {
  return (
    <span className="flex min-w-0 flex-col items-center gap-1 text-center">
      {asTag ? <TeamTag name={name} /> : <span className="text-base font-bold break-words">{name}</span>}
      <span className="text-sm text-muted">
        {status.icon && <span aria-hidden="true">{status.icon} </span>}
        {status.text}
      </span>
    </span>
  );
}

/** Cartão de um mapa (BO1 avulso, mapa de BO3 ou mapa antigo). */
export function MapCardItem({ card, href }: { card: MapCard; href: string }) {
  const winner = card.winner;
  const scoreText = card.verified ? `${card.score_left} a ${card.score_right}` : "sem placar verificado";
  return (
    <li className="card group relative flex min-h-48 flex-col p-4 hover:bg-surface-2">
      <div className="flex items-center justify-between gap-2">
        <h3 className="text-base font-extrabold tracking-wider">{card.map}</h3>
        <time className="text-sm text-muted" dateTime={card.date ?? undefined}>
          {card.date_label}
        </time>
      </div>
      <div className="my-4 grid flex-1 grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-2">
        <Side name={card.left} status={sideStatus(winner, "left")} />
        <span className="flex items-center gap-2">
          <Score value={card.score_left} win={winner === "left"} loss={winner === "right"} />
          <span aria-hidden="true" className="text-xl text-muted">:</span>
          <Score value={card.score_right} win={winner === "right"} loss={winner === "left"} />
        </span>
        <Side name={card.right} status={sideStatus(winner, "right")} />
      </div>
      <div className="flex items-center justify-between gap-2 border-t border-line-soft pt-3 text-sm">
        <span className="text-muted">{card.verified ? "Placar verificado" : "Placar pendente"}</span>
        <Link
          href={href}
          className="font-bold after:absolute after:inset-0 after:content-['']"
        >
          <span className="sr-only">
            {card.map}, {card.date_label}, {card.left} {scoreText} {card.right}.{" "}
          </span>
          Ver estatísticas →
        </Link>
      </div>
    </li>
  );
}

/** Cartão de um confronto BO1 ou BO3 com situação e placar da série. */
export function SeriesCardItem({
  series,
  href,
  active,
}: {
  series: SeriesCard;
  href: string;
  active: boolean;
}) {
  const fmt = series.format.toUpperCase();
  const winner = series.winner;
  const scoreText =
    series.score_left !== null && series.score_right !== null
      ? `${series.score_left} a ${series.score_right}`
      : "sem placar";
  return (
    <li
      className={clsx(
        "card group relative flex flex-col gap-2 p-3 hover:bg-surface-2",
        active && "border-accent ring-2 ring-accent",
      )}
    >
      <div className="flex items-center justify-between gap-2">
        <h3 className="text-base font-extrabold">
          {fmt} · {series.date_label}
        </h3>
        <Badge tone={series.complete ? "accent" : "neutral"}>{series.status}</Badge>
      </div>
      <div className="grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-2">
        <Side name={series.left} status={sideStatus(winner, "left")} asTag />
        <span className="flex items-center gap-2">
          <Score value={series.score_left} win={winner === "left"} loss={winner === "right"} />
          <span aria-hidden="true" className="text-xl text-muted">×</span>
          <Score value={series.score_right} win={winner === "right"} loss={winner === "left"} />
        </span>
        <Side name={series.right} status={sideStatus(winner, "right")} asTag />
      </div>
      <div className="flex flex-wrap items-center justify-between gap-x-3 text-base">
        <p className="text-muted">{series.summary}</p>
        <Link
          href={href}
          aria-current={active ? "true" : undefined}
          className="inline-flex min-h-11 items-center font-bold after:absolute after:inset-0 after:content-['']"
        >
          <span className="sr-only">
            {fmt} de {series.date_label}: {series.left} {scoreText} {series.right}.{" "}
          </span>
          {active ? "Fechar ↑" : "Ver mapas ↓"}
        </Link>
      </div>
    </li>
  );
}
