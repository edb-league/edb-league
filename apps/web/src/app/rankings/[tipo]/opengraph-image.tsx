import { api, qs } from "@/lib/api";
import { num } from "@/lib/format";
import { OG_SIZE, OG_TYPE, ogImage } from "@/lib/og/card";
import type { Ranking } from "@/lib/types";

export const alt = "Ranking da EDB LEAGUE";
export const size = OG_SIZE;
export const contentType = OG_TYPE;

const TYPES = new Set(["elite", "superacao", "xp", "bagres"]);

export default async function Image({ params }: { params: Promise<{ tipo: string }> }) {
  const { tipo } = await params;
  if (!TYPES.has(tipo)) return ogImage({ kicker: "Rankings", title: "Rankings" });
  try {
    const ranking = await api<Ranking>(`/rankings/${tipo}${qs({})}`);
    const decimals = ranking.type === "xp" ? 0 : 1;
    return ogImage({
      kicker: ranking.season.label,
      title: ranking.title,
      subtitle: ranking.rows.length ? undefined : "Ainda sem partidas nesta temporada",
      rows: ranking.rows.length
        ? ranking.rows.slice(0, 3).map((r) => ({ rank: r.rank, name: r.name, value: num(r.focus, decimals, ranking.focus_unit) }))
        : undefined,
    });
  } catch {
    return ogImage({ kicker: "Rankings", title: "Rankings", subtitle: "Elite, Superação, XP e BAGRES" });
  }
}
