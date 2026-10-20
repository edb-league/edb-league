import { NextResponse, type NextRequest } from "next/server";

/**
 * Mantém funcionando os links antigos do app Streamlit (?page=..., ?player=..., ?match=...),
 * redirecionando de forma permanente para as rotas novas.
 */
const PAGES: Record<string, string> = {
  home: "/",
  rankings: "/rankings/elite",
  matches: "/partidas",
  players: "/jogadores",
  versus: "/comparar",
  fame: "/hall-da-fama",
  medals: "/medalhas",
  xp: "/missoes-xp",
  admin: "/admin",
};

export function proxy(request: NextRequest) {
  const { searchParams } = request.nextUrl;
  const legacy = ["page", "player", "match", "bo3", "ranking", "season"].some((k) => searchParams.has(k));
  if (!legacy) return NextResponse.next();

  const url = request.nextUrl.clone();
  url.search = "";
  const season = searchParams.get("season");
  const player = searchParams.get("player");
  const match = searchParams.get("match");
  const bo3 = searchParams.get("bo3");
  const page = searchParams.get("page") ?? "home";
  const ranking = searchParams.get("ranking");

  if (player) {
    url.pathname = `/jogadores/${encodeURIComponent(player)}`;
  } else if (match) {
    url.pathname = `/partidas/mapa/${encodeURIComponent(match)}`;
    if (bo3) url.searchParams.set("confronto", bo3);
  } else if (page === "rankings") {
    const type = ranking === "resenha" ? "bagres" : ranking === "superacao" ? "superacao" : "elite";
    url.pathname = `/rankings/${type}`;
  } else {
    url.pathname = PAGES[page] ?? "/";
    if (page === "matches" && bo3) url.searchParams.set("confronto", bo3);
  }
  if (season && /^\d+$/.test(season) && url.pathname !== "/jogadores" && !url.pathname.startsWith("/jogadores/")) {
    url.searchParams.set("temporada", season);
  }
  return NextResponse.redirect(url, 308);
}

export const config = { matcher: ["/"] };
