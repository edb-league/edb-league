export type NavItem = {
  href: string;
  label: string;
  /** Prefixo de rota que marca o item como ativo. */
  match: string;
};

export const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "Visão geral", match: "/" },
  { href: "/rankings/elite", label: "Rankings", match: "/rankings" },
  { href: "/partidas", label: "Partidas", match: "/partidas" },
  { href: "/jogadores", label: "Jogadores", match: "/jogadores" },
  { href: "/comparar", label: "Comparar jogadores", match: "/comparar" },
  { href: "/hall-da-fama", label: "Hall da Fama", match: "/hall-da-fama" },
  { href: "/medalhas", label: "Medalhas", match: "/medalhas" },
  { href: "/missoes-xp", label: "Missões & XP", match: "/missoes-xp" },
];

export function isActive(pathname: string, item: NavItem): boolean {
  if (item.match === "/") return pathname === "/";
  return pathname === item.match || pathname.startsWith(item.match + "/");
}
