"use client";

import clsx from "clsx";
import { useEffect, useMemo, useRef, useState, useSyncExternalStore } from "react";
import { controlClass } from "@/components/ui/Field";
import { Notice } from "@/components/ui/Notice";
import { skinImageUrl, type CatalogSkin } from "@/lib/skins";
import {
  CATEGORIES, INVENTORY, RARITY_BORDER, SIDE_LABEL, categoryOf, compareWeapons, sidesOf,
  type Category, type InventoryItem, type Side,
} from "./inventory-data";

const PAGE = 48;
const STORAGE_KEY = "edb-skins-previa-v1";
const STORAGE_EVENT = "edb-skins-previa";
const CATEGORY_LABEL = Object.fromEntries(CATEGORIES.map((c) => [c.id, c.label])) as Record<Category, string>;

/** Silhueta simples para arma sem skin escolhida (não é arte de nenhuma arma real). */
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

/** `models` só existe nos slots de faca e luvas: cada lado usa uma faca (e um par de luvas) e o modelo é escolhido dentro dele. */
type Weapon = { key: string; name: string; category: Category; sides: Side[]; skins: InventoryItem[]; models?: Weapon[] };

const SLOT_NAME: Partial<Record<Category, string>> = { knife: "Faca", gloves: "Luvas" };

/* A escolha de skin é uma prévia: fica só neste navegador. Guardada fora do React para sobreviver a recarregamentos. */
function subscribe(callback: () => void) {
  window.addEventListener("storage", callback);
  window.addEventListener(STORAGE_EVENT, callback);
  return () => {
    window.removeEventListener("storage", callback);
    window.removeEventListener(STORAGE_EVENT, callback);
  };
}
function readStored(): string {
  try {
    return window.localStorage.getItem(STORAGE_KEY) ?? "";
  } catch {
    return "";
  }
}
function parseChoices(raw: string): Record<string, string> {
  try {
    const data: unknown = JSON.parse(raw || "{}");
    return data && typeof data === "object" && !Array.isArray(data) ? (data as Record<string, string>) : {};
  } catch {
    return {};
  }
}

function SkinCard({ item, selected, onSelect }: { item: InventoryItem; selected: boolean; onSelect: () => void }) {
  return (
    <li>
      <button
        type="button"
        aria-pressed={selected}
        onClick={onSelect}
        style={item.color ? { borderBottomColor: item.color } : undefined}
        className={clsx(
          "relative flex h-full min-h-44 w-full flex-col items-center justify-between gap-2 rounded-xl border border-b-4 bg-surface-2 p-3 text-center transition hover:bg-surface-3",
          selected ? "border-accent" : "border-line-soft",
          !item.color && (item.rarity ? RARITY_BORDER[item.rarity] : "border-b-transparent"),
        )}
      >
        {selected && <span className="absolute right-2 top-2 rounded-md bg-accent-bg px-2 py-0.5 text-sm font-bold text-on-accent">Em uso</span>}
        {item.image ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={item.image} alt="" loading="lazy" width={160} height={120} className="mt-4 h-24 w-auto max-w-full object-contain" />
        ) : (
          <Silhouette category={item.category} />
        )}
        <span className="text-lg font-bold">{item.skin}</span>
      </button>
    </li>
  );
}

/**
 * Inventário de skins no estilo "uma casa por arma": lado (TR/CT), tipo de arma, busca e, ao abrir uma arma,
 * as skins dela. A escolha é uma prévia salva neste navegador; ainda não é ligada ao servidor (WeaponPaints).
 */
export function SkinInventory({ catalog = [] }: { catalog?: CatalogSkin[] }) {
  const [side, setSide] = useState<Side>("t");
  const [category, setCategory] = useState<Category | "all">("all");
  const [query, setQuery] = useState("");
  const [openKey, setOpenKey] = useState<string | null>(null);
  const [modelKey, setModelKey] = useState<string | null>(null);
  const [rarity, setRarity] = useState("");
  const [skinQuery, setSkinQuery] = useState("");
  const [limit, setLimit] = useState(PAGE);
  const [session, setSession] = useState<Record<string, string>>({});
  const stored = useSyncExternalStore(subscribe, readStored, () => "");
  const returnTo = useRef<string | null>(null);
  const returnModel = useRef<string | null>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const gridRef = useRef<HTMLUListElement>(null);

  const source = useMemo<InventoryItem[]>(() => {
    if (catalog.length === 0) return INVENTORY;
    return catalog.flatMap((skin) => {
      const cat = categoryOf(skin.category);
      return cat
        ? [{ id: skin.id, category: cat, weapon: skin.weapon, skin: skin.name, image: skinImageUrl(skin.image), color: skin.rarity_color || undefined, rarityName: skin.rarity }]
        : [];
    });
  }, [catalog]);

  const weapons = useMemo<Weapon[]>(() => {
    const map = new Map<string, Weapon>();
    for (const item of source) {
      const key = `${item.category}|${item.weapon}`;
      let weapon = map.get(key);
      if (!weapon) {
        weapon = { key, name: item.weapon, category: item.category, sides: sidesOf(item.weapon), skins: [] };
        map.set(key, weapon);
      }
      if (item.skin) weapon.skins.push(item);
    }
    const order = new Map(CATEGORIES.map((c, i) => [c.id, i]));
    const sorted = [...map.values()]
      .map((w) => ({ ...w, skins: [...w.skins].sort((a, b) => (a.skin ?? "").localeCompare(b.skin ?? "", "en")) }))
      .sort((a, b) => (order.get(a.category)! - order.get(b.category)!) || compareWeapons(a.name, b.name));
    // Faca e luvas viram um slot único por lado; os modelos (Karambit, Talon...) ficam dentro dele.
    const out: Weapon[] = [];
    for (const w of sorted) {
      const slotName = SLOT_NAME[w.category];
      if (!slotName) {
        out.push(w);
        continue;
      }
      const slotKey = `slot|${w.category}`;
      let slot = out.find((x) => x.key === slotKey);
      if (!slot) {
        slot = { key: slotKey, name: slotName, category: w.category, sides: ["t", "ct"], skins: [], models: [] };
        out.push(slot);
      }
      slot.models!.push(w);
      slot.skins.push(...w.skins);
    }
    return out;
  }, [source]);

  const choices = useMemo(() => {
    const merged = { ...parseChoices(stored), ...session };
    return merged;
  }, [stored, session]);

  function choose(weapon: Weapon, skinId: string | null) {
    const key = `${side}:${weapon.key}`;
    const merged = { ...parseChoices(readStored()), ...session, [key]: skinId ?? "" };
    setSession((prev) => ({ ...prev, [key]: skinId ?? "" }));
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(merged));
      window.dispatchEvent(new Event(STORAGE_EVENT));
    } catch {
      /* sem armazenamento (janela privada): a escolha vale só até recarregar a página */
    }
  }

  const q = query.trim().toLowerCase();
  const visibleWeapons = useMemo(
    () => weapons.filter((w) => w.sides.includes(side)
      && (category === "all" || w.category === category)
      && (!q || w.name.toLowerCase().includes(q)
        || w.models?.some((m) => m.name.toLowerCase().includes(q))
        || w.skins.some((s) => (s.skin ?? "").toLowerCase().includes(q)))),
    [weapons, side, category, q],
  );

  const open = openKey ? weapons.find((w) => w.key === openKey) ?? null : null;
  const model = open?.models && modelKey ? open.models.find((m) => m.key === modelKey) ?? null : null;
  // Lista de skins na tela: a do modelo aberto (faca/luvas) ou a da própria arma.
  const viewSkins = useMemo(() => (open ? (open.models ? model?.skins ?? [] : open.skins) : []), [open, model]);
  const pickingModel = Boolean(open?.models && !model);
  const rarities = useMemo(
    () => [...new Set(viewSkins.map((s) => s.rarityName).filter((r): r is string => Boolean(r)))].sort(),
    [viewSkins],
  );
  const skins = useMemo(() => {
    const sq = skinQuery.trim().toLowerCase();
    return viewSkins.filter((s) => (!rarity || s.rarityName === rarity) && (!sq || (s.skin ?? "").toLowerCase().includes(sq)));
  }, [viewSkins, rarity, skinQuery]);
  const shownSkins = skins.slice(0, limit);
  const chosenId = open ? choices[`${side}:${open.key}`] : undefined;
  const chosenSkin = chosenId && open ? open.skins.find((s) => s.id === chosenId) : undefined;
  const models = useMemo(() => {
    if (!open?.models) return [];
    const sq = skinQuery.trim().toLowerCase();
    return open.models.filter((m) => !sq || m.name.toLowerCase().includes(sq) || m.skins.some((s) => (s.skin ?? "").toLowerCase().includes(sq)));
  }, [open, skinQuery]);

  // Ao abrir uma arma ou modelo o foco vai para o título; ao voltar, para a casa que estava aberta.
  useEffect(() => {
    if (open && !model && returnModel.current) {
      gridRef.current?.querySelector<HTMLElement>(`[data-model="${CSS.escape(returnModel.current)}"]`)?.focus();
      returnModel.current = null;
    } else if (open) titleRef.current?.focus();
    else if (returnTo.current) {
      const target = gridRef.current?.querySelector<HTMLElement>(`[data-weapon="${CSS.escape(returnTo.current)}"]`);
      target?.focus();
      returnTo.current = null;
    }
  }, [open, model]);

  function openWeapon(weapon: Weapon) {
    setRarity("");
    setSkinQuery("");
    setLimit(PAGE);
    setModelKey(null);
    setOpenKey(weapon.key);
  }
  function openModel(m: Weapon) {
    setRarity("");
    setSkinQuery("");
    setLimit(PAGE);
    setModelKey(m.key);
  }
  function closeWeapon() {
    if (model) {
      returnModel.current = model.key;
      setSkinQuery("");
      setModelKey(null);
      return;
    }
    returnTo.current = openKey;
    setOpenKey(null);
  }

  return (
    <section aria-labelledby="inventario" className="flex flex-col gap-4">
      <h2 id="inventario" className="text-3xl">Inventário</h2>
      <Notice tone="info">
        {catalog.length > 0
          ? "Catálogo de skins do CS2. A skin que você marca aqui é uma prévia, salva só neste navegador. Para valer no servidor, escolha no jogo com !skins."
          : "Prévia do layout com itens de exemplo. O catálogo de skins ainda não foi carregado."}
      </Notice>

      <div className="flex flex-wrap items-center gap-3">
        <div role="group" aria-label="Lado" className="flex gap-2">
          {(["t", "ct"] as const).map((s) => (
            <button
              key={s}
              type="button"
              aria-pressed={side === s}
              onClick={() => setSide(s)}
              className={clsx(
                "min-h-11 min-w-16 rounded-lg border-2 px-4 text-lg font-bold transition",
                side === s ? (s === "t" ? "border-gold bg-surface-3 text-gold" : "border-accent bg-surface-3 text-accent") : "border-line-soft bg-surface-2 text-muted hover:border-accent",
              )}
            >
              {SIDE_LABEL[s]}
            </button>
          ))}
        </div>
        <div role="group" aria-label="Tipo de arma" className="flex flex-wrap gap-2">
          {[{ id: "all" as const, label: "Todas" }, ...CATEGORIES].map((c) => (
            <button
              key={c.id}
              type="button"
              aria-pressed={category === c.id}
              onClick={() => { setCategory(c.id); setOpenKey(null); setModelKey(null); }}
              className={clsx("min-h-11 rounded-lg border px-3 text-base font-bold transition", category === c.id ? "border-gold bg-surface-3 text-gold" : "border-line-soft bg-surface-2 text-muted hover:border-accent")}
            >
              {c.label}
            </button>
          ))}
        </div>
        {!open && (
          <label className="w-full sm:ml-auto sm:w-64">
            <span className="sr-only">Pesquisar arma ou skin</span>
            <input type="search" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Pesquisar arma ou skin" className={controlClass} />
          </label>
        )}
      </div>

      {open ? (
        <div className="flex flex-col gap-4">
          <div className="flex flex-wrap items-center gap-3">
            <button type="button" onClick={closeWeapon} className="min-h-11 rounded-lg border border-line-soft bg-surface-2 px-3 text-base font-bold text-muted transition hover:border-accent hover:text-fg">
              {model ? "← Modelos" : "← Armas"}
            </button>
            <h3 ref={titleRef} tabIndex={-1} className="text-2xl font-bold focus-visible:outline-offset-4">
              {model ? model.name : open.name} <span className="text-lg font-normal text-muted">({SIDE_LABEL[side]} · {model ? open.name : CATEGORY_LABEL[open.category]})</span>
            </h3>
            {chosenId && (
              <button type="button" onClick={() => choose(open, null)} className="min-h-11 rounded-lg border border-line-soft bg-surface-2 px-3 text-base font-bold text-muted transition hover:border-accent hover:text-fg sm:ml-auto">
                Voltar para a skin padrão
              </button>
            )}
          </div>
          {pickingModel && (
            <>
              <div className="flex flex-wrap items-center gap-3">
                <label className="w-full sm:w-64">
                  <span className="sr-only">Pesquisar modelo ou skin</span>
                  <input type="search" value={skinQuery} onChange={(e) => setSkinQuery(e.target.value)} placeholder="Pesquisar modelo ou skin" className={controlClass} />
                </label>
                <p role="status" className="text-base text-muted">{models.length} {models.length === 1 ? "modelo" : "modelos"}</p>
              </div>
              <p className="text-base text-muted">Cada lado usa um só item de {open.name.toLowerCase()}. Escolha o modelo e depois a skin; a escolha troca a anterior.</p>
              {models.length === 0 ? (
                <p className="rounded-xl border border-dashed border-line p-6 text-center text-muted" role="status">Nenhum modelo encontrado.</p>
              ) : (
                <ul ref={gridRef} className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6">
                  {models.map((m) => {
                    const current = chosenSkin && m.skins.some((s) => s.id === chosenSkin.id) ? chosenSkin : undefined;
                    return (
                      <li key={m.key}>
                        <button
                          type="button"
                          data-model={m.key}
                          onClick={() => openModel(m)}
                          style={current?.color ? { borderBottomColor: current.color } : undefined}
                          className={clsx(
                            "relative flex h-full min-h-44 w-full flex-col items-center justify-between gap-2 rounded-xl border border-b-4 bg-surface-2 p-3 text-center transition hover:border-accent hover:bg-surface-3",
                            current ? "border-accent" : "border-line-soft border-b-transparent",
                          )}
                        >
                          {current && <span className="absolute right-2 top-2 rounded-md bg-accent-bg px-2 py-0.5 text-sm font-bold text-on-accent">Em uso</span>}
                          {current?.image ? (
                            // eslint-disable-next-line @next/next/no-img-element
                            <img src={current.image} alt="" loading="lazy" width={160} height={120} className="mt-4 h-24 w-auto max-w-full object-contain" />
                          ) : (
                            <Silhouette category={m.category} />
                          )}
                          <span className="flex flex-col">
                            <span className="text-lg font-bold">{m.name}</span>
                            <span className="text-sm text-muted">{current ? current.skin : `${m.skins.length} ${m.skins.length === 1 ? "skin" : "skins"}`}</span>
                          </span>
                        </button>
                      </li>
                    );
                  })}
                </ul>
              )}
            </>
          )}
          {!pickingModel && viewSkins.length > 0 && (
            <div className="flex flex-wrap items-center gap-3">
              <label className="w-full sm:w-64">
                <span className="sr-only">Pesquisar skin</span>
                <input type="search" value={skinQuery} onChange={(e) => { setSkinQuery(e.target.value); setLimit(PAGE); }} placeholder="Pesquisar skin" className={controlClass} />
              </label>
              {rarities.length > 1 && (
                <label className="flex items-center gap-2 text-base text-muted">
                  Raridade
                  <select value={rarity} onChange={(e) => { setRarity(e.target.value); setLimit(PAGE); }} className={clsx(controlClass, "w-auto")}>
                    <option value="">Todas</option>
                    {rarities.map((r) => <option key={r} value={r}>{r}</option>)}
                  </select>
                </label>
              )}
              <p role="status" className="text-base text-muted">{skins.length} {skins.length === 1 ? "skin" : "skins"}</p>
            </div>
          )}
          {pickingModel ? null : viewSkins.length === 0 ? (
            <p className="rounded-xl border border-dashed border-line p-6 text-center text-muted" role="status">{model ? "Este modelo" : "Esta arma"} ainda não tem skins no catálogo.</p>
          ) : shownSkins.length === 0 ? (
            <p className="rounded-xl border border-dashed border-line p-6 text-center text-muted" role="status">Nenhuma skin encontrada.</p>
          ) : (
            <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6">
              {shownSkins.map((item) => (
                <SkinCard key={item.id} item={item} selected={chosenId === item.id} onSelect={() => choose(open, chosenId === item.id ? null : item.id)} />
              ))}
              {skins.length > shownSkins.length && (
                <li>
                  <button type="button" onClick={() => setLimit((n) => n + PAGE)} className="flex h-full min-h-44 w-full items-center justify-center rounded-xl border border-line-soft bg-surface-2 p-3 text-lg font-bold text-muted transition hover:border-accent hover:bg-surface-3">
                    Mostrar mais ({skins.length - shownSkins.length})
                  </button>
                </li>
              )}
            </ul>
          )}
        </div>
      ) : (
        <>
          <p role="status" className="text-base text-muted">{visibleWeapons.length} {visibleWeapons.length === 1 ? "item" : "itens"} no lado {SIDE_LABEL[side]}</p>
          {visibleWeapons.length === 0 ? (
            <p className="rounded-xl border border-dashed border-line p-6 text-center text-muted">Nenhum item encontrado.</p>
          ) : (
            <ul ref={gridRef} className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6">
              {visibleWeapons.map((weapon) => {
                const skinId = choices[`${side}:${weapon.key}`];
                const skin = skinId ? weapon.skins.find((s) => s.id === skinId) : undefined;
                const skinModel = skin ? weapon.models?.find((m) => m.skins.some((s) => s.id === skin.id)) : undefined;
                return (
                  <li key={weapon.key}>
                    <button
                      type="button"
                      data-weapon={weapon.key}
                      onClick={() => openWeapon(weapon)}
                      style={skin?.color ? { borderBottomColor: skin.color } : undefined}
                      className={clsx(
                        "flex h-full min-h-44 w-full flex-col items-center justify-between gap-2 rounded-xl border border-b-4 bg-surface-2 p-3 text-center transition hover:border-accent hover:bg-surface-3",
                        skin ? "border-line" : "border-line-soft border-b-transparent",
                      )}
                    >
                      {skin?.image ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img src={skin.image} alt="" loading="lazy" width={160} height={120} className="h-24 w-auto max-w-full object-contain" />
                      ) : (
                        <Silhouette category={weapon.category} />
                      )}
                      <span className="flex flex-col">
                        <span className="text-sm text-muted">{weapon.models ? "★ " : ""}{weapon.name}{skinModel ? ` · ${skinModel.name}` : ""}</span>
                        <span className="text-lg font-bold">{skin?.skin ?? (weapon.models ? `${weapon.name} padrão` : "Skin padrão")}</span>
                        <span className="text-sm text-muted">
                          {weapon.models
                            ? `${weapon.models.length} ${weapon.models.length === 1 ? "modelo" : "modelos"}`
                            : `${weapon.skins.length} ${weapon.skins.length === 1 ? "skin" : "skins"}`}
                        </span>
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </>
      )}
    </section>
  );
}
