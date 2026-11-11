import clsx from "clsx";
import { Avatar } from "@/components/ui/Avatar";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, SectionTitle } from "@/components/ui/Card";
import type { DraftPlayer, DraftTeam, DraftView } from "@/lib/types";

type Live = Extract<DraftView, { exists: true }>;

function PlayerRow({ player, avatars, tag, muted }: { player: DraftPlayer; avatars: Record<string, string>; tag?: string; muted?: boolean }) {
  return (
    <li className={clsx("flex items-center gap-3 rounded-lg border border-line-soft bg-surface-2 p-2", muted && "opacity-70")}>
      <Avatar name={player.name} src={avatars[player.id]} size={40} level={player.level} decorative />
      <span className="min-w-0 flex-1 truncate text-base font-bold">{player.name}</span>
      {tag && <span className="shrink-0 text-sm text-muted">{tag}</span>}
    </li>
  );
}

function TeamCard({ team, size, active, avatars }: { team: DraftTeam; size: number; active: boolean; avatars: Record<string, string> }) {
  const empty = Math.max(0, size - 1 - team.picks.length);
  return (
    <Card aria-labelledby={`time-${team.id}`} className={clsx("flex flex-col gap-3", active && "ring-2 ring-[var(--focus)]")}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 id={`time-${team.id}`} className="font-display text-2xl font-bold uppercase">{team.name}</h3>
        {active ? <Badge tone="gold">Na vez</Badge> : null}
      </div>
      <ul className="flex flex-col gap-2">
        <PlayerRow player={team.captain} avatars={avatars} tag="Capitão" />
        {team.picks.map((pick) => (
          <PlayerRow key={pick.player.id} player={pick.player} avatars={avatars} tag={`Escolha ${pick.number}`} />
        ))}
        {Array.from({ length: empty }, (_, i) => (
          <li key={`vaga-${i}`} className="flex min-h-14 items-center rounded-lg border border-dashed border-line-soft px-3 text-base text-muted">
            Vaga aberta
          </li>
        ))}
      </ul>
      <p className="text-sm text-muted">Soma dos níveis: <span className="num font-bold text-fg">{team.level_sum}</span></p>
    </Card>
  );
}

/** Quadro do draft: vez atual, times e jogadores disponíveis. Com `onPick`, cada disponível ganha um botão de escolha (administração). */
export function DraftBoard({
  view,
  avatars = {},
  onPick,
  busy,
}: {
  view: Live;
  avatars?: Record<string, string>;
  onPick?: (playerId: string) => void;
  busy?: boolean;
}) {
  const done = view.status === "done";
  return (
    <div className="flex flex-col gap-6">
      <Card aria-labelledby="draft-vez" className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 id="draft-vez" className="text-3xl">{view.name}</h2>
          <p className="mt-1 text-lg" role="status">
            {done ? (
              "Draft encerrado. Os times estão fechados."
            ) : view.next ? (
              <>
                Escolha <span className="num font-bold">{view.next.number}</span> de <span className="num font-bold">{view.next.total}</span>: vez do time{" "}
                <span className="font-bold">{view.next.team_name}</span>.
              </>
            ) : null}
          </p>
        </div>
        <Badge tone={done ? "win" : "gold"}>{done ? "Encerrado" : "Em andamento"}</Badge>
      </Card>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {view.teams.map((team) => (
          <TeamCard key={team.id} team={team} size={view.team_size} active={view.next?.team_id === team.id} avatars={avatars} />
        ))}
      </div>

      <Card aria-labelledby="draft-disponiveis">
        <SectionTitle id="draft-disponiveis" title="Jogadores disponíveis">
          {view.available.length === 0 ? "Todos os jogadores já foram escolhidos." : `${view.available.length} ainda sem time, do maior nível para o menor.`}
        </SectionTitle>
        {view.available.length > 0 && (
          <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {view.available.map((player) => (
              <li key={player.id} className="flex items-center gap-3 rounded-lg border border-line-soft bg-surface-2 p-2">
                <Avatar name={player.name} src={avatars[player.id]} size={40} level={player.level} decorative />
                <span className="min-w-0 flex-1 truncate text-base font-bold">{player.name}</span>
                {onPick && view.next && (
                  <Button variant="gold" disabled={busy} onClick={() => onPick(player.id)} aria-label={`Escolher ${player.name} para o time ${view.next.team_name}`}>
                    Escolher
                  </Button>
                )}
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
