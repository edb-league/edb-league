import { api } from "@/lib/api";
import { OG_SIZE, OG_TYPE, ogImage } from "@/lib/og/card";
import type { MatchDetail } from "@/lib/types";

export const alt = "Resultado de partida na EDB LEAGUE";
export const size = OG_SIZE;
export const contentType = OG_TYPE;

export default async function Image({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  try {
    const { match } = await api<MatchDetail>(`/matches/${encodeURIComponent(id)}`);
    return ogImage({
      kicker: match.date_label,
      title: match.map,
      versus: {
        left: match.left,
        right: match.right,
        scoreLeft: match.score_left,
        scoreRight: match.score_right,
        winner: match.winner,
      },
    });
  } catch {
    return ogImage({ kicker: "Partida", title: "Resultado", subtitle: "Placar e estatísticas na EDB LEAGUE" });
  }
}
