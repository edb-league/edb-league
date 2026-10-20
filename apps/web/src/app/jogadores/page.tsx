import Link from "next/link";
import { PageHeader } from "@/components/ui/PageHeader";
import { EmptyState } from "@/components/ui/Card";
import { api } from "@/lib/api";
import type { Meta, PlayerListItem } from "@/lib/types";

export const metadata = { title: "Jogadores" };

export default async function PlayersPage() {
  const [meta, players] = await Promise.all([api<Meta>("/meta"), api<PlayerListItem[]>("/players")]);
  const sorted = [...players].sort((a, b) => a.name.localeCompare(b.name, "pt-BR"));

  return (
    <>
      <PageHeader
        title="Perfil dos jogadores"
        subtitle="Foto da Steam, horas de CS e estatísticas de cada jogador."
        counts={{ players: meta.counts.players, matches: meta.counts.matches, maps: meta.counts.maps }}
      />
      {sorted.length === 0 ? (
        <EmptyState>Cadastre os participantes na área de Administração.</EmptyState>
      ) : (
        <section aria-labelledby="lista">
          <h2 id="lista" className="sr-only">Lista de jogadores</h2>
          <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {sorted.map((p) => (
              <li key={p.id} className="card group relative flex items-center justify-between gap-3 p-4 hover:bg-surface-2">
                <div className="min-w-0">
                  <p className="text-lg font-bold break-words">
                    <Link
                      href={`/jogadores/${encodeURIComponent(p.id)}`}
                      className="text-fg no-underline group-hover:underline after:absolute after:inset-0 after:content-['']"
                    >
                      {p.name}
                    </Link>
                  </p>
                  <p className="text-base text-muted">Nível {p.level}</p>
                </div>
                <span aria-hidden="true" className="text-xl text-muted">→</span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </>
  );
}
