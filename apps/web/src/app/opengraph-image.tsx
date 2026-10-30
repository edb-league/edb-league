import { OG_SIZE, OG_TYPE, ogImage } from "@/lib/og/card";

export const alt = "EDB LEAGUE · liga de Counter-Strike 2";
export const size = OG_SIZE;
export const contentType = OG_TYPE;

export default function Image() {
  return ogImage({
    kicker: "Liga de Counter-Strike 2",
    title: "EDB LEAGUE",
    subtitle: "Rankings Elite, Superação e XP · partidas · jogadores · medalhas",
  });
}
