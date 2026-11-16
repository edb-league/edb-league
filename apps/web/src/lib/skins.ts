/** Catálogo de skins guardado no nosso Supabase Storage (gerado pelo workflow "Importar imagens das skins"). */
export type CatalogSkin = {
  id: string;
  weapon_id: number | null;
  weapon: string;
  category: string;
  name: string;
  rarity: string;
  rarity_color: string;
  /** Mesmo número que o WeaponPaints usa para a skin. */
  paint_index: string;
  /** Caminho da imagem dentro do bucket. */
  image: string;
};

export const SKINS_STORAGE_URL = (
  process.env.SKINS_STORAGE_URL ?? "https://cgopqcbgxpzurejtjmbu.supabase.co/storage/v1/object/public/skins"
).replace(/\/$/, "");

export function skinImageUrl(path: string): string {
  return `${SKINS_STORAGE_URL}/${path}`;
}

/** Lê o catálogo no servidor (cache de 5 minutos). Qualquer falha devolve lista vazia e a página usa o layout de exemplo. */
export async function getSkinCatalog(): Promise<CatalogSkin[]> {
  try {
    const response = await fetch(`${SKINS_STORAGE_URL}/catalog.json`, { next: { revalidate: 300 } });
    if (!response.ok) return [];
    const data: unknown = await response.json();
    return Array.isArray(data) ? (data as CatalogSkin[]).filter((s) => s && typeof s.id === "string" && typeof s.image === "string") : [];
  } catch {
    return [];
  }
}
