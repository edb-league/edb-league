import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/Card";
import { controlClass } from "@/components/ui/Field";
import { LevelBadge } from "@/components/ui/LevelBadge";
import { PageHeader } from "@/components/ui/PageHeader";
import { api, qs } from "@/lib/api";
import { first, num } from "@/lib/format";
import { seasonContext } from "@/lib/season";
import type { PlayerListItem, Ranking, RankingRow } from "@/lib/types";

export const metadata = { title: "Jogadores" };

const LEVEL_BANDS = {
  "1-3": [1, 3],
  "4-6": [4, 6],
  "7-8": [7, 8],
  "9-10": [9, 10],
} as const;
type Band = keyof typeof LEVEL_BANDS;

const SORTS = {
  elite: "Índice Elite",
  nome: "Nome",
  nivel: "Nível",
  kd: "K/D",
  adr: "ADR",
} as const;
type SortKey = keyof typeof SORTS;

type Entry = { player: PlayerListItem; row: RankingRow | null };

function sortEntries(entries: Entry[], key: SortKey): Entry[] {
  const byName = (a: Entry, b: Entry) => a.player.name.localeCompare(b.player.name, "pt-BR");
  const desc = (pick: (e: Entry) => number | null) => (a: Entry, b: Entry) => {
    const x = pick(a), y = pick(b);
    if (x === null && y === null) return byName(a, b);
    if (x === null) return 1;
    if (y === null) return -1;
    return y - x || byName(a, b);
  };
  const sorted = [...entries];
  if (key === "nome") return sorted.sort(byName);
  if (key === "nivel") return sorted.sort(desc((e) => e.player.level));
  if (key === "kd") return sorted.sort(desc((e) => e.row?.kd ?? null));
  if (key === "adr") return sorted.sort(desc((e) => e.row?.adr ?? null));
  return sorted.sort(desc((e) => e.row?.elite ?? null));
}

export default async function PlayersPage({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const sp = await searchParams;
  const { meta, season } = await seasonContext(sp.temporada);
  const [players, elite] = await Promise.all([
    api<PlayerListItem[]>("/players"),
    api<Ranking>(`/rankings/elite${qs({ season })}`),
  ]);

  const query = (first(sp.q) ?? "").trim();
  const bandRaw = first(sp.nivel) ?? "";
  const band = (bandRaw in LEVEL_BANDS ? bandRaw : "") as Band | "";
  const sortRaw = first(sp.ordem) ?? "elite";
  const sort = (sortRaw in SORTS ? sortRaw : "elite") as SortKey;

  const rows = new Map(elite.rows.map((r) => [r.player_id, r]));
  const norm = (t: string) => t.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  const all: Entry[] = players.map((player) => ({ player, row: rows.get(player.id) ?? null }));
  const shown = sortEntries(
    all.filter(({ player }) => {
      if (query && !norm(player.name).includes(norm(query))) return false;
      if (band) {
        const [lo, hi] = LEVEL_BANDS[band];
        if (player.level < lo || player.level > hi) return false;
      }
      return true;
    }),
    sort,
  );
  const filtered = Boolean(query || band);

  return (
    <>
      <PageHeader
        title="Jogadores"
        subtitle="Foto da Steam, horas de CS e estatísticas de cada jogador."
        counts={{ players: meta.counts.players, matches: meta.counts.matches, maps: meta.counts.maps }}
      />

      <form method="get" role="search" aria-label="Buscar jogadores" className="card flex flex-wrap items-end gap-4 p-4">
        {sp.temporada !== undefined && <input type="hidden" name="temporada" value={String(first(sp.temporada))} />}
        <div className="flex min-w-56 flex-1 flex-col gap-1.5">
          <label htmlFor="q" className="text-base font-bold">Buscar jogador</label>
          <input id="q" name="q" type="search" defaultValue={query} placeholder="Nick ou nome" className={controlClass} />
        </div>
        <div className="flex min-w-40 flex-col gap-1.5">
          <label htmlFor="nivel" className="text-base font-bold">Nível</label>
          <select id="nivel" name="nivel" defaultValue={band} className={controlClass}>
            <option value="">Todos</option>
            {Object.keys(LEVEL_BANDS).map((b) => (
              <option key={b} value={b}>Níveis {b}</option>
            ))}
          </select>
        </div>
        <div className="flex min-w-44 flex-col gap-1.5">
          <label htmlFor="ordem" className="text-base font-bold">Ordenar por</label>
          <select id="ordem" name="ordem" defaultValue={sort} className={controlClass}>
            {Object.entries(SORTS).map(([key, label]) => (
              <option key={key} value={key}>{label}</option>
            ))}
          </select>
        </div>
        <Button type="submit" variant="gold">Aplicar</Button>
        {(filtered || sort !== "elite") && (
          <Link href="/jogadores" className="inline-flex min-h-11 items-center text-base font-bold">Limpar</Link>
        )}
      </form>

      <section aria-labelledby="lista">
        <h2 id="lista" className="sr-only">Lista de jogadores</h2>
        <p role="status" className="mb-3 text-base text-muted">
          {shown.length} de {all.length} {all.length === 1 ? "jogador" : "jogadores"}. Estatísticas e posição da {elite.season.label}.
        </p>
        {shown.length === 0 ? (
          <EmptyState>
            {all.length === 0 ? "Cadastre os participantes na área de Administração." : "Nenhum jogador encontrado com esses filtros."}
          </EmptyState>
        ) : (
          <ul className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {shown.map(({ player: p, row }) => {
              const top = row !== null && row.rank <= 3;
              return (
                <li
                  key={p.id}
                  className={`card group relative flex flex-col gap-3 p-4 hover:bg-surface-2 ${top ? "border-2 border-gold-bg" : ""}`}
                >
                  <div className="flex items-start gap-3">
                    <LevelBadge level={p.level} size="lg" />
                    <div className="min-w-0 flex-1">
                      <h3 className="text-2xl leading-tight font-bold break-words">
                        <Link
                          href={`/jogadores/${encodeURIComponent(p.id)}`}
                          className="text-fg no-underline group-hover:underline after:absolute after:inset-0 after:content-['']"
                        >
                          {p.nickname}
                        </Link>
                      </h3>
                      {p.real_name && <p className="text-base text-muted">{p.real_name}</p>}
                    </div>
                    {row && (
                      <span className="num rounded-lg border border-line-soft bg-surface-2 px-2 py-1 text-xl leading-none text-gold">
                        <span className="sr-only">Posição no Elite </span>
                        {row.rank}º
                      </span>
                    )}
                  </div>
                  {row ? (
                    <dl className="grid grid-cols-3 gap-2 border-t border-line-soft pt-3">
                      <div>
                        <dt className="text-sm text-muted">Elite</dt>
                        <dd className="num text-3xl leading-none text-gold">{num(row.elite, 1)}</dd>
                      </div>
                      <div>
                        <dt className="text-sm text-muted">K/D</dt>
                        <dd className="num text-3xl leading-none">{num(row.kd, 2)}</dd>
                      </div>
                      <div>
                        <dt className="text-sm text-muted">ADR</dt>
                        <dd className="num text-3xl leading-none">{num(row.adr, 1)}</dd>
                      </div>
                    </dl>
                  ) : (
                    <p className="border-t border-line-soft pt-3 text-base text-muted">Sem partidas na {elite.season.label}.</p>
                  )}
                  {!p.is_active && <p className="text-sm text-muted">Fora do elenco ativo</p>}
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </>
  );
}
