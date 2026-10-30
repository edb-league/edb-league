import { api } from "@/lib/api";
import { num } from "@/lib/format";
import { OG_SIZE, OG_TYPE, ogImage } from "@/lib/og/card";
import type { PlayerDetail } from "@/lib/types";

export const alt = "Perfil de jogador na EDB LEAGUE";
export const size = OG_SIZE;
export const contentType = OG_TYPE;

export default async function Image({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  try {
    const { player, summary } = await api<PlayerDetail>(`/players/${encodeURIComponent(id)}`);
    return ogImage({
      kicker: "Jogador",
      title: player.nickname,
      subtitle: [player.real_name, `Nível ${player.level}`].filter(Boolean).join(" · "),
      stars: player.stars,
      stats: [
        { label: "Mapas jogados", value: num(summary.games) },
        { label: "Vitórias", value: num(summary.win_rate, 0, "%") },
        { label: "Kills por round", value: num(summary.kpr, 2) },
        { label: "Dano por round", value: num(summary.adr, 1) },
      ],
    });
  } catch {
    return ogImage({ kicker: "Jogador", title: "Perfil", subtitle: "Estatísticas, medalhas e histórico na EDB LEAGUE" });
  }
}
