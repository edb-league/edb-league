import Link from "next/link";
import { AchievementTabs } from "@/components/layout/SectionTabs";
import { SeasonBar } from "@/components/layout/SeasonBar";
import { Card, SectionTitle } from "@/components/ui/Card";
import { Avatar } from "@/components/ui/Avatar";
import { Badge, YouBadge } from "@/components/ui/Badge";
import { getMe } from "@/lib/me";
import { Progress } from "@/components/ui/Charts";
import { LevelBadge } from "@/components/ui/LevelBadge";
import { PageHeader } from "@/components/ui/PageHeader";
import { Stat } from "@/components/ui/Stat";
import { TableWrap, Td, Th } from "@/components/ui/Table";
import { api, qs, steamAvatars } from "@/lib/api";
import { dayMonth, num, plural, seasonQuery } from "@/lib/format";
import { seasonContext } from "@/lib/season";
import type { MissionPlayer, Missions } from "@/lib/types";
import { Icon, StarRow } from "@/components/ui/Icon";

export const metadata = { title: "Missões e XP" };

export default async function MissionsPage({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const { meta, season } = await seasonContext((await searchParams).temporada);
  const [missions, avatars, me] = await Promise.all([api<Missions>(`/missions${qs({ season })}`), steamAvatars(), getMe()]);
  const top = missions.xp.rows.slice(0, 5);

  return (
    <>
      <PageHeader
        title="Missões e conquistas"
        subtitle="Todo nível tem uma meta. O prêmio é igual; o desafio é proporcional."
        art="xp"
      >
        <SeasonBar meta={meta} season={season} path="/missoes-xp" variant="strip" />
      </PageHeader>
      <AchievementTabs current="/missoes-xp" />

      <Card aria-labelledby="meta-semanal">
        <SectionTitle id="meta-semanal" title="Meta semanal: kills por round">
          Concluir uma partida de pelo menos 8 rounds com KPR igual ou acima da meta rende 100 XP, uma vez a cada semana da temporada.
        </SectionTitle>
        <dl className="grid grid-cols-2 gap-3 sm:grid-cols-5">
          {missions.targets.map((t) => (
            <Stat key={t.stars} label={`${t.stars} ${t.stars === 1 ? "estrela" : "estrelas"}`} value={`${num(t.kpr, 2)} KPR`} />
          ))}
        </dl>
        <p className="mt-4 text-base text-muted">
          Presença, vitórias e o limite de XP por temporada estão no{" "}
          <Link href="/regulamento#xp">Regulamento</Link>.
        </p>
      </Card>

      {missions.week && missions.players.length > 0 && <WeekMission missions={missions} avatars={avatars} meId={me.player?.id} />}

      <section aria-labelledby="xp-ranking">
        <SectionTitle id="xp-ranking" title="Quem lidera em XP">
          Os cinco primeiros do ranking de experiência desta temporada.
        </SectionTitle>
        {top.length ? (
          <TableWrap caption="Cinco primeiros do ranking de experiência">
            <thead>
              <tr>
                <Th>#</Th>
                <Th>Jogador</Th>
                <Th>Nível</Th>
                <Th numeric>Partidas</Th>
                <Th numeric>XP</Th>
              </tr>
            </thead>
            <tbody>
              {top.map((r) => (
                <tr key={r.player_id}>
                  <Td className="num text-2xl text-muted">{r.rank}</Td>
                  <Td className="font-bold">
                    <Link href={`/jogadores/${encodeURIComponent(r.player_id)}`} className="text-fg">{r.name}</Link>
                  </Td>
                  <Td><LevelBadge level={r.level} /></Td>
                  <Td numeric>{num(r.matches)}</Td>
                  <Td numeric className="num text-2xl text-gold">{num(r.xp)}</Td>
                </tr>
              ))}
            </tbody>
          </TableWrap>
        ) : (
          <p className="text-base text-muted">O ranking aparece após as primeiras partidas.</p>
        )}
        <p className="mt-3">
          <Link href={`/rankings/xp${seasonQuery(season)}`} className="link-cta">
            Ver o ranking XP completo <Icon name="arrow-right" />
          </Link>
        </p>
      </section>
    </>
  );
}

const STATUS_TEXT: Record<MissionPlayer["status"], string> = {
  done: "Cumprida",
  unselected: "Meta batida, fora dos 6 mapas do XP",
  open: "Ainda não bateu a meta",
  none: "Sem partidas na semana",
};

function WeekMission({ missions, avatars, meId }: { missions: Missions; avatars: Record<string, string>; meId?: string }) {
  const week = missions.week!;
  const done = missions.players.filter((p) => p.status === "done").length;
  return (
    <section aria-labelledby="missao-semana">
      <SectionTitle id="missao-semana" title={`Missão da semana ${week.number} de ${week.total}`}>
        {dayMonth(week.starts_on)} a {dayMonth(week.ends_on)} ·{" "}
        {week.closed ? "semana encerrada" : week.days_left === 0 ? "último dia" : `faltam ${plural(week.days_left, "dia", "dias")}`} ·{" "}
        <b className="text-fg">{done}</b> de {missions.players.length} já cumpriram.
      </SectionTitle>
      <ul className="card divide-y divide-line-soft">
        {missions.players.map((p) => {
          const pct = p.status === "done" || p.status === "unselected" ? 100 : p.best_kpr ? Math.min(99, (100 * p.best_kpr) / p.target) : 0;
          return (
            <li
              key={p.player.id}
              className={`grid grid-cols-[minmax(0,1fr)] items-center gap-x-4 gap-y-2 px-4 py-3 md:grid-cols-[minmax(0,15rem)_minmax(0,1fr)_auto] ${p.player.id === meId ? "bg-surface-2" : ""}`}
            >
              <div className="flex min-w-0 items-center gap-3">
                <Avatar name={p.player.name} src={avatars[p.player.id]} size={44} level={p.level} decorative className="border-2" />
                <div className="min-w-0">
                  <Link href={`/jogadores/${encodeURIComponent(p.player.id)}`} className="block truncate text-lg leading-tight font-bold text-fg">
                    {p.player.name}
                  </Link>
                  {p.player.id === meId && <YouBadge />}
                  <p className="text-sm text-muted">
                    <span role="img" aria-label={`${p.stars} ${p.stars === 1 ? "estrela" : "estrelas"}`} className="text-gold">
                      <StarRow count={p.stars} />
                    </span>{" "}
                    meta {num(p.target, 2)} KPR
                  </p>
                </div>
              </div>
              <div className="min-w-0">
                <Progress value={pct} tone={p.status === "done" ? "gold" : "accent"} label={`Progresso da missão de ${p.player.name}`} />
                <p className="mt-1 text-sm text-muted">
                  {p.status === "open" && p.best_kpr !== null
                    ? `Melhor KPR da semana: ${num(p.best_kpr, 2)} de ${num(p.target, 2)}`
                    : p.status === "none"
                      ? "Nenhuma partida de 8 rounds ou mais ainda"
                      : p.best_kpr !== null
                        ? `Melhor KPR da semana: ${num(p.best_kpr, 2)}`
                        : ""}
                </p>
              </div>
              <div className="md:text-right">
                {p.status === "done" ? (
                  <Badge tone="win">
                    <Icon name="check" /> {STATUS_TEXT.done} · +100 XP
                  </Badge>
                ) : p.status === "unselected" ? (
                  <Badge tone="gold">{STATUS_TEXT.unselected}</Badge>
                ) : (
                  <Badge>{STATUS_TEXT[p.status]}</Badge>
                )}
              </div>
            </li>
          );
        })}
      </ul>
      <p className="mt-3 text-sm text-muted">
        Só valem os mapas de pelo menos 8 rounds que entram entre os 6 do ranking de XP do jogador. Se a meta foi batida em um mapa
        que ficou de fora, a missão não rende XP.
      </p>
    </section>
  );
}
