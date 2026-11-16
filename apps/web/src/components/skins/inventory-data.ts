/** Dados de EXEMPLO do inventário (só o layout). Quando o seletor for ligado, estes itens vêm da API. */
export type Category = "knife" | "gloves" | "rifle" | "sniper" | "pistol" | "smg" | "shotgun" | "mg";
export type Rarity = "consumer" | "industrial" | "milspec" | "restricted" | "classified" | "covert" | "gold";

export type InventoryItem = {
  id: string;
  category: Category;
  weapon: string;
  skin?: string;
  rarity?: Rarity;
  /** Imagem (catálogo) e cor da raridade vindas do catálogo. */
  image?: string;
  color?: string;
  /** Nome da raridade no catálogo (ex.: "Covert"), usado no filtro. */
  rarityName?: string;
  /** Números do WeaponPaints (arma e pintura), usados para gravar a skin no servidor. */
  weaponId?: number;
  paintId?: number;
};

export const CATEGORIES: { id: Category; label: string }[] = [
  { id: "knife", label: "Facas" },
  { id: "gloves", label: "Luvas" },
  { id: "rifle", label: "Rifles" },
  { id: "sniper", label: "Snipers" },
  { id: "pistol", label: "Pistolas" },
  { id: "smg", label: "SMGs" },
  { id: "shotgun", label: "Escopetas" },
  { id: "mg", label: "Metralhadoras" },
];

const w = (category: Category, weapon: string, skin?: string, rarity?: Rarity): InventoryItem => ({
  id: `${category}-${weapon}`.toLowerCase().replace(/[^a-z0-9]+/g, "-"),
  category, weapon, skin, rarity,
});

export const INVENTORY: InventoryItem[] = [
  w("knife", "Karambit", "Doppler Ruby", "gold"),
  w("knife", "M9 Bayonet", "Gamma Doppler Emerald", "gold"),
  w("knife", "Butterfly Knife"),
  w("gloves", "Sport Gloves", "Hedge Maze", "gold"),
  w("gloves", "Specialist Gloves", "Crimson Kimono", "gold"),
  w("rifle", "AK-47", "Bloodsport", "covert"),
  w("rifle", "M4A1-S"),
  w("rifle", "M4A4"),
  w("rifle", "FAMAS"),
  w("rifle", "Galil AR"),
  w("rifle", "AUG"),
  w("rifle", "SG 553"),
  w("sniper", "AWP", "Asiimov", "covert"),
  w("sniper", "SSG 08"),
  w("sniper", "SCAR-20"),
  w("sniper", "G3SG1"),
  w("pistol", "Desert Eagle"),
  w("pistol", "USP-S"),
  w("pistol", "Glock-18"),
  w("pistol", "P250"),
  w("pistol", "Five-SeveN"),
  w("pistol", "Tec-9"),
  w("pistol", "CZ75-Auto"),
  w("pistol", "P2000"),
  w("pistol", "Dual Berettas"),
  w("pistol", "R8 Revolver"),
  w("smg", "MP9"),
  w("smg", "MAC-10"),
  w("smg", "MP7"),
  w("smg", "MP5-SD"),
  w("smg", "UMP-45"),
  w("smg", "P90"),
  w("smg", "PP-Bizon"),
  w("shotgun", "Nova"),
  w("shotgun", "XM1014"),
  w("shotgun", "MAG-7"),
  w("shotgun", "Sawed-Off"),
  w("mg", "M249"),
  w("mg", "Negev"),
];

/** Cor da borda inferior de cada raridade (só enfeite; o nome da skin é o que identifica o item). */
export const RARITY_BORDER: Record<Rarity, string> = {
  consumer: "border-b-[#b0c3d9]",
  industrial: "border-b-[#5e98d9]",
  milspec: "border-b-[#4b69ff]",
  restricted: "border-b-[#8847ff]",
  classified: "border-b-[#d32ce6]",
  covert: "border-b-[#eb4b4b]",
  gold: "border-b-[#e4ae39]",
};

/** Tipo de arma a partir do nome da categoria do catálogo (em inglês). A ordem importa: "sniper rifles" antes de "rifles". */
export function categoryOf(name: string): Category | null {
  const n = name.toLowerCase();
  if (n.includes("knife") || n.includes("knives")) return "knife";
  if (n.includes("glove")) return "gloves";
  if (n.includes("sniper")) return "sniper";
  if (n.includes("rifle")) return "rifle";
  if (n.includes("pistol")) return "pistol";
  if (n.includes("smg") || n.includes("submachine")) return "smg";
  if (n.includes("shotgun")) return "shotgun";
  if (n.includes("machine")) return "mg";
  return null;
}

export type Side = "ct" | "t";

/** Armas que só um dos lados usa no CS2. Quem não está aqui (facas, luvas, AWP, Desert Eagle, P250...) vale para os dois. */
const CT_ONLY = ["m4a1s", "m4a4", "usps", "p2000", "fiveseven", "mp9", "mag7", "famas", "aug", "scar20"];
const T_ONLY = ["ak47", "glock18", "tec9", "mac10", "galilar", "sg553", "sawedoff", "g3sg1"];

function weaponKey(weapon: string): string {
  return weapon.toLowerCase().replace(/[^a-z0-9]/g, "");
}

/** Lados que podem usar a arma. */
export function sidesOf(weapon: string): Side[] {
  const key = weaponKey(weapon);
  if (CT_ONLY.includes(key)) return ["ct"];
  if (T_ONLY.includes(key)) return ["t"];
  return ["ct", "t"];
}

/** Ordem das armas dentro de cada tipo (as mais usadas primeiro). O que não está aqui vem depois, em ordem alfabética. */
const WEAPON_ORDER = [
  "karambit", "m9bayonet", "butterflyknife", "flipknife", "bayonet", "huntsmanknife", "talon", "sportgloves", "specialistgloves",
  "ak47", "m4a1s", "m4a4", "famas", "galilar", "aug", "sg553",
  "awp", "ssg08", "scar20", "g3sg1",
  "desert eagle", "usps", "glock18", "p2000", "p250", "fiveseven", "tec9", "cz75auto",
  "mp9", "mac10", "mp7", "ump45", "p90", "ppbizon", "mp5sd",
  "nova", "xm1014", "mag7", "sawedoff", "m249", "negev",
].map((w) => weaponKey(w));

export function compareWeapons(a: string, b: string): number {
  const ia = WEAPON_ORDER.indexOf(weaponKey(a));
  const ib = WEAPON_ORDER.indexOf(weaponKey(b));
  if (ia !== ib) return (ia === -1 ? 999 : ia) - (ib === -1 ? 999 : ib);
  return a.localeCompare(b, "en");
}

export const SIDE_LABEL: Record<Side, string> = { t: "TR", ct: "CT" };
