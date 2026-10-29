import clsx from "clsx";
import Link from "next/link";
import { Badge, TeamTag } from "@/components/ui/Badge";
import type { MapCard, SeriesCard } from "@/lib/types";
import { NoData } from "@/components/ui/NoData";
import { Icon, type IconName } from "@/components/ui/Icon";
import { Fmt, MapTile } from "@/components/ui/MapTile";

function sideStatus(winner: "left" | "right" | null, side: "left" | "right"): { text: string; icon: IconName | null } {
  if (winner === null) return { text: "Equipe", icon: null };
  return winner === side ? { text: "Vencedor", icon: "check" } : { text: "Derrotado", icon: "x" };
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
  status: { text: string; icon: IconName | null };
  asTag?: boolean;
}) {
  return (
    <span className="flex min-w-0 flex-col items-center gap-1 text-center">
      {asTag ? <TeamTag name={name} /> : <span className="text-base font-bold break-words">{name}</span>}
      <span className="text-sm text-muted">
        {status.icon && <Icon name={status.icon} />}{status.icon && " "}
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
    <li className="card group relative flex min-h-48 flex-col overflow-hidden card-press hover:bg-surface-2">
      <MapTile map={card.map} className="flex items-center justify-between gap-2 px-4 py-3">
        <h3 className="font-display text-2xl leading-none font-bold">{card.map}</h3>
        <time className="rounded-full bg-surface/80 px-2.5 py-0.5 text-sm text-muted" dateTime={card.date ?? undefined}>
          {card.date_label}
        </time>
      </MapTile>
      <div className="mx-4 my-4 grid flex-1 grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-2">
        <Side name={card.left} status={sideStatus(winner, "left")} />
        <span className="flex items-center gap-2">
          <Score value={card.score_left} win={winner === "left"} loss={winner === "right"} />
          <span aria-hidden="true" className="text-xl text-muted">:</span>
          <Score value={card.score_right} win={winner === "right"} loss={winner === "left"} />
        </span>
        <Side name={card.right} status={sideStatus(winner, "right")} />
      </div>
      <div className="mx-4 mb-4 flex items-center justify-between gap-2 border-t border-line-soft pt-3 text-sm">
        <span className="text-muted">{card.verified ? "Placar verificado" : "Placar pendente"}</span>
        <Link
          href={href}
          className="font-bold after:absolute after:inset-0 after:content-['']"
        >
          <span className="sr-only">
            {card.map}, {card.date_label}, {card.left} {scoreText} {card.right}.{" "}
          </span>
          Ver estatísticas <Icon name="arrow-right" />
        </Link>
      </div>
    </li>
  );
}

function RowName({ name, win }: { name: string; win: boolean }) {
  return (
    <span className="inline-flex items-center gap-1 text-base font-bold">
      {win && <Icon name="check" className="text-win" />}
      {name}
    </span>
  );
}

/** Linha compacta de um mapa, para listar os mapas de um confronto logo abaixo do cartão da série. */
export function MapRowItem({ card, href }: { card: MapCard; href: string }) {
  const winner = card.winner;
  const scoreText = card.verified ? `${card.score_left} a ${card.score_right}` : "sem placar verificado";
  return (
    <li className="card group relative flex items-stretch overflow-hidden card-press hover:bg-surface-2">
      <MapTile map={card.map} compact className="flex w-28 shrink-0 flex-col justify-center py-2 pr-2 pl-6 sm:w-36">
        <h3 className="font-display text-xl leading-none font-bold">{card.map}</h3>
        <time className="mt-1 text-sm text-muted" dateTime={card.date ?? undefined}>
          {card.date_label}
        </time>
      </MapTile>
      <div className="flex min-w-0 flex-1 items-center justify-center gap-2 px-2 py-3 sm:gap-4">
        <RowName name={card.left} win={winner === "left"} />
        <span className="flex items-center gap-1.5">
          <Score value={card.score_left} win={winner === "left"} loss={winner === "right"} />
          <span aria-hidden="true" className="text-lg text-muted">:</span>
          <Score value={card.score_right} win={winner === "right"} loss={winner === "left"} />
        </span>
        <RowName name={card.right} win={winner === "right"} />
      </div>
      <Link href={href} className="flex shrink-0 items-center px-3 text-base font-bold after:absolute after:inset-0 after:content-['']">
        <span className="sr-only">
          {card.map}, {card.date_label}, {card.left} {scoreText} {card.right}. Ver estatísticas{" "}
        </span>
        <Icon name="arrow-right" className="size-5" />
      </Link>
    </li>
  );
}

/** Cartão de um confronto BO1 ou BO3 com situação e placar da série. */
export function SeriesCardItem({
  series,
  href,
  active,
  children,
}: {
  series: SeriesCard;
  href: string;
  active: boolean;
  /** Mapas do confronto: aparecem logo abaixo do cartão quando ele está aberto. */
  children?: React.ReactNode;
}) {
  const fmt = series.format.toUpperCase();
  const winner = series.winner;
  const mapNames = series.maps.map((m) => m.map);
  const scoreText =
    series.score_left !== null && series.score_right !== null
      ? `${series.score_left} a ${series.score_right}`
      : "sem placar";
  return (
    <li id={`confronto-${series.id}`} className="scroll-mt-4">
    <div
      className={clsx(
        "card group relative flex flex-col gap-2 p-3 card-press hover:bg-surface-2",
        active && "border-accent ring-2 ring-accent",
      )}
    >
      <div className="flex items-center justify-between gap-2">
        <h3 className="text-base font-extrabold">
          <Fmt format={series.format} /> · {series.date_label}
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
      {mapNames.length > 1 && (
        <ul className="flex gap-1.5" aria-hidden="true">
          {series.maps.map((m) => (
            <li key={m.id} className="min-w-0 flex-1">
              <MapTile map={m.map} compact className="h-8 rounded-md border border-line-soft pr-2 pl-5">
                <span className="block truncate font-display text-base leading-8 font-bold">{m.map}</span>
              </MapTile>
            </li>
          ))}
        </ul>
      )}
      <div className="flex flex-wrap items-center justify-between gap-x-3 text-base">
        <p className="text-muted">{series.summary}</p>
        <Link
          href={href}
          aria-current={active ? "true" : undefined}
          className="link-cta after:absolute after:inset-0 after:content-['']"
        >
          <span className="sr-only">
            {fmt} de {series.date_label}: {series.left} {scoreText} {series.right}.{" "}
          </span>
          {active ? <>Fechar <Icon name="arrow-up" /></> : <>Ver mapas <Icon name="arrow-down" /></>}
        </Link>
      </div>
    </div>
    {active && children && (
      <div className="reveal-list mt-2 ml-3 border-l-2 border-accent pl-3 md:ml-4 md:pl-4">{children}</div>
    )}
    </li>
  );
}
