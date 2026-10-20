export type NavItem = {
  href: string;
  label: string;
  /** Prefixo de rota que marca o item como ativo. */
  match: string;
  /** Item principal fica sempre visível no menu superior; os demais ficam em "Mais". */
  primary?: boolean;
};

export const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "Início", match: "/", primary: true },
  { href: "/rankings/elite", label: "Rankings", match: "/rankings", primary: true },
  { href: "/partidas", label: "Partidas", match: "/partidas", primary: true },
  { href: "/jogadores", label: "Jogadores", match: "/jogadores", primary: true },
  { href: "/comparar", label: "Comparar", match: "/comparar", primary: true },
  { href: "/hall-da-fama", label: "Hall da Fama", match: "/hall-da-fama" },
  { href: "/medalhas", label: "Medalhas", match: "/medalhas" },
  { href: "/missoes-xp", label: "Missões e XP", match: "/missoes-xp" },
];

export function isActive(pathname: string, item: NavItem): boolean {
  if (item.match === "/") return pathname === "/";
  return pathname === item.match || pathname.startsWith(item.match + "/");
}
