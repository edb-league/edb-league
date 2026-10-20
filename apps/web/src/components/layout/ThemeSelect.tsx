"use client";

import { useId, useSyncExternalStore } from "react";
import { controlClass } from "@/components/ui/Field";

type Theme = "auto" | "light" | "dark";
const KEY = "edb-theme";

const listeners = new Set<() => void>();
/** Escolha feita nesta visita; vale mesmo quando o navegador bloqueia o armazenamento. */
let chosen: Theme | null = null;

function apply(theme: Theme) {
  const root = document.documentElement;
  if (theme === "auto") root.removeAttribute("data-theme");
  else root.setAttribute("data-theme", theme);
}

function read(): Theme {
  if (chosen) return chosen;
  try {
    const saved = localStorage.getItem(KEY);
    if (saved === "light" || saved === "dark") return saved;
  } catch {
    /* armazenamento indisponível */
  }
  return "auto";
}

function subscribe(callback: () => void) {
  listeners.add(callback);
  window.addEventListener("storage", callback);
  return () => {
    listeners.delete(callback);
    window.removeEventListener("storage", callback);
  };
}

function choose(next: Theme) {
  chosen = next;
  apply(next);
  try {
    if (next === "auto") localStorage.removeItem(KEY);
    else localStorage.setItem(KEY, next);
  } catch {
    /* sem armazenamento: vale só nesta visita */
  }
  listeners.forEach((callback) => callback());
}

/** Tema automático (segue o sistema), claro ou escuro. A escolha fica no navegador. */
export function ThemeSelect() {
  const id = useId();
  const theme = useSyncExternalStore(subscribe, read, () => "auto" as Theme);

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-sm text-muted">
        Tema
      </label>
      <select id={id} className={controlClass} value={theme} onChange={(event) => choose(event.target.value as Theme)}>
        <option value="auto">Automático (sistema)</option>
        <option value="light">Claro</option>
        <option value="dark">Escuro</option>
      </select>
    </div>
  );
}
