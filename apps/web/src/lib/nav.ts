export type NavLink = {
  href: string;
  label: string;
  /** Prefixo de rota que marca o item como ativo. */
  match: string;
};

export type NavGroup = { label: string; items: NavLink[] };
export type NavEntry = NavLink | NavGroup;

export const isGroup = (entry: NavEntry): entry is NavGroup => "items" in entry;

const L = (href: string, label: string, match = href): NavLink => ({ href, label, match });

/** Estrutura do menu superior: itens diretos e dois grupos. */
export const NAV: NavEntry[] = [
  L("/", "Início"),
  L("/rankings/elite", "Rankings", "/rankings"),
  L("/partidas", "Partidas"),
  L("/jogadores", "Jogadores"),
  { label: "Conquistas", items: [L("/medalhas", "Medalhas"), L("/missoes-xp", "Missões e XP"), L("/hall-da-fama", "Hall da Fama"), L("/temporadas", "Temporadas")] },
  { label: "Ferramentas", items: [L("/sorteador", "Sorteador de times"), L("/comparar", "Comparar jogadores")] },
  L("/regulamento", "Regulamento"),
];

/** Todos os links, na ordem do menu (rodapé). */
export const NAV_ITEMS: NavLink[] = NAV.flatMap((e) => (isGroup(e) ? e.items : [e]));

/** Abas da área Conquistas (mesmas três páginas do grupo do menu). */
export const ACHIEVEMENT_TABS: NavLink[] = (NAV.find((e) => isGroup(e) && e.label === "Conquistas") as NavGroup).items;

export function isActive(pathname: string, item: NavLink): boolean {
  if (item.match === "/") return pathname === "/";
  return pathname === item.match || pathname.startsWith(item.match + "/");
}
