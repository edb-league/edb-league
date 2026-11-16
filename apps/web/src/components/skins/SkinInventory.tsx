"use client";

import clsx from "clsx";
import { useMemo, useState } from "react";
import { controlClass } from "@/components/ui/Field";
import { Notice } from "@/components/ui/Notice";
import { CATEGORIES, INVENTORY, RARITY_BORDER, type Category, type InventoryItem } from "./inventory-data";

const FIRST_PAGE = 11;

/** Silhueta simples para quem ainda não tem skin (não é arte de nenhuma arma real). */
function Silhouette({ category }: { category: Category }) {
  const long = category === "rifle" || category === "sniper" || category === "smg" || category === "shotgun" || category === "mg";
  return (
    <svg aria-hidden="true" viewBox="0 0 120 48" className="h-12 w-28 fill-current text-surface-3">
      {category === "knife" ? (
        <path d="M14 30 78 12c10-3 22 1 28 10l-60 12-28 4z" />
      ) : category === "gloves" ? (
        <path d="M34 40V20l8-10 8 8 8-8 8 8 8-8 8 10v20c0 4-4 6-8 6H42c-4 0-8-2-8-6z" />
      ) : long ? (
        <path d="M4 22h70l8-8h18l6 6v6l-6 4H80l-6 12H60l4-12H44l-8 10H24l6-14H4z" />
      ) : (
        <path d="M30 14h56l6 8v8H70l-4 14H52l4-14H30z" />
      )}
    </svg>
  );
}

function Card({ item, selected, onSelect }: { item: InventoryItem; selected: boolean; onSelect: () => void }) {
  const owned = Boolean(item.skin);
  return (
    <li>
      <button
        type="button"
        aria-pressed={selected}
        onClick={onSelect}
        className={clsx(
          "flex h-full min-h-40 w-full flex-col items-center justify-between gap-2 rounded-xl border border-b-4 bg-surface-2 p-3 text-center transition hover:bg-surface-3",
          selected ? "border-accent" : "border-line-soft",
          owned && item.rarity ? RARITY_BORDER[item.rarity] : "border-b-transparent",
        )}
      >
        <Silhouette category={item.category} />
        <span className="flex flex-col">
          <span className={clsx("text-sm", owned ? "text-muted" : "text-lg font-bold text-muted")}>
            {item.category === "knife" || item.category === "gloves" ? "★ " : ""}{item.weapon}
          </span>
          {owned && <span className="text-lg font-bold">{item.skin}</span>}
        </span>
      </button>
    </li>
  );
}

/** Inventário de skins: abas por tipo de arma, busca e grade. Layout pronto; os itens são de exemplo até ligarmos ao seletor. */
export function SkinInventory() {
  const [category, setCategory] = useState<Category | "all">("all");
  const [query, setQuery] = useState("");
  const [showAll, setShowAll] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);

  const items = useMemo(() => {
    const q = query.trim().toLowerCase();
    return INVENTORY.filter((i) => (category === "all" || i.category === category)
      && (!q || i.weapon.toLowerCase().includes(q) || (i.skin ?? "").toLowerCase().includes(q)));
  }, [category, query]);

  const limited = category === "all" && !query && !showAll;
  const visible = limited ? items.slice(0, FIRST_PAGE) : items;

  return (
    <section aria-labelledby="inventario" className="flex flex-col gap-4">
      <h2 id="inventario" className="text-3xl">Inventário</h2>
      <Notice tone="info">Prévia do layout com itens de exemplo. As suas skins aparecem aqui quando o seletor for conectado.</Notice>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div role="group" aria-label="Tipo de arma" className="flex flex-wrap gap-2">
          {[{ id: "all" as const, label: "Todas" }, ...CATEGORIES].map((c) => (
            <button
              key={c.id}
              type="button"
              aria-pressed={category === c.id}
              onClick={() => { setCategory(c.id); setShowAll(false); }}
              className={clsx("min-h-11 rounded-lg border px-3 text-base font-bold transition", category === c.id ? "border-gold bg-surface-3 text-gold" : "border-line-soft bg-surface-2 text-muted hover:border-accent")}
            >
              {c.label}
            </button>
          ))}
        </div>
        <label className="w-full sm:w-64">
          <span className="sr-only">Pesquisar por nome</span>
          <input type="search" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Pesquisar por nome" className={controlClass} />
        </label>
      </div>

      {visible.length === 0 ? (
        <p className="rounded-xl border border-dashed border-line p-6 text-center text-muted" role="status">Nenhum item encontrado.</p>
      ) : (
        <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6">
          {visible.map((item) => (
            <Card key={item.id} item={item} selected={selected === item.id} onSelect={() => setSelected(selected === item.id ? null : item.id)} />
          ))}
          {limited && items.length > FIRST_PAGE && (
            <li>
              <button type="button" onClick={() => setShowAll(true)} className="flex h-full min-h-40 w-full items-center justify-center rounded-xl border border-line-soft bg-surface-2 p-3 text-lg font-bold text-muted transition hover:border-accent hover:bg-surface-3">
                Mostrar todas ({items.length})
              </button>
            </li>
          )}
        </ul>
      )}
    </section>
  );
}
