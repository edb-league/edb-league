/** Dados de EXEMPLO do inventário (só o layout). Quando o seletor for ligado, estes itens vêm da API. */
export type Category = "knife" | "gloves" | "rifle" | "sniper" | "pistol" | "smg" | "shotgun" | "mg";
export type Rarity = "consumer" | "industrial" | "milspec" | "restricted" | "classified" | "covert" | "gold";

export type InventoryItem = { id: string; category: Category; weapon: string; skin?: string; rarity?: Rarity };

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
