import { TeamDraw, type RosterPlayer } from "@/components/tools/TeamDraw";
import { Card } from "@/components/ui/Card";
import { PageHeader } from "@/components/ui/PageHeader";
import { api, steamAvatars } from "@/lib/api";
import type { PlayerListItem } from "@/lib/types";

export const metadata = { title: "Sorteador de times" };

export default async function DrawPage() {
  const [players, avatars] = await Promise.all([api<PlayerListItem[]>("/players"), steamAvatars()]);
  const roster: RosterPlayer[] = players
    .filter((p) => p.is_active)
    .map((p) => ({ id: p.id, name: p.name, nickname: p.nickname, real_name: p.real_name, level: p.level, avatar: avatars[p.id] }))
    // Do maior nível para o menor; no mesmo nível, ordem alfabética.
    .sort((a, b) => b.level - a.level || a.nickname.localeCompare(b.nickname, "pt-BR"));

  return (
    <>
      <PageHeader
        title="Sorteador de times"
        subtitle="Escolha os 10 presentes. O sorteio divide em PT e PL com a menor diferença possível na soma dos níveis."
      />
      <TeamDraw roster={roster} />
      <Card aria-labelledby="como">
        <h2 id="como" className="text-3xl">Como funciona</h2>
        <ol className="mt-3 max-w-prose list-decimal space-y-1.5 pl-6 text-lg text-muted">
          <li>Escolha exatamente 10 jogadores presentes.</li>
          <li>
            O sorteio escolhe, ao acaso, uma das divisões 5 × 5 com a menor diferença possível na soma dos níveis (1 a 10).
          </li>
          <li>Os níveis vêm do cadastro da liga.</li>
          <li>Nada é gravado: o resultado não altera classificações nem registra partidas.</li>
        </ol>
      </Card>
    </>
  );
}
