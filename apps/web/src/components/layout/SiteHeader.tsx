"use client";

import clsx from "clsx";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useId, useState } from "react";
import { NAV_ITEMS, isActive } from "@/lib/nav";
import { ThemeSelect } from "./ThemeSelect";

function LockIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="5" y="10" width="14" height="11" rx="2" />
      <path d="M8 10V7a4 4 0 0 1 8 0v3" />
    </svg>
  );
}

/**
 * Cabeçalho do site. Em telas largas vira a coluna lateral fixa; em telas estreitas é uma
 * barra no topo com botão de menu (aria-expanded). Existe um único landmark <nav>.
 */
export function SiteHeader() {
  const pathname = usePathname();
  // O menu aberto fica atrelado à rota em que foi aberto: ao navegar, fecha sozinho.
  const [openOn, setOpenOn] = useState<string | null>(null);
  const open = openOn === pathname;
  const setOpen = (value: boolean | ((current: boolean) => boolean)) => {
    const next = typeof value === "function" ? value(open) : value;
    setOpenOn(next ? pathname : null);
  };
  const panelId = useId();

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpenOn(null);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  const adminActive = pathname.startsWith("/admin");

  return (
    <header className="sticky top-0 z-40 border-b border-line-soft bg-surface lg:fixed lg:inset-y-0 lg:left-0 lg:flex lg:w-64 lg:flex-col lg:overflow-y-auto lg:border-r lg:border-b-0">
      <div className="flex items-center justify-between gap-3 px-4 py-2 lg:px-5 lg:py-5">
        <Link href="/" className="flex items-center gap-3 rounded-lg text-fg no-underline" aria-label="EDB LEAGUE, página inicial">
          <Image src="/crest.webp" alt="" width={44} height={44} priority className="size-11 object-contain" />
          <span className="text-lg font-extrabold tracking-wide">EDB LEAGUE</span>
        </Link>
        <button
          type="button"
          className="inline-flex min-h-11 items-center gap-2 rounded-lg border border-line bg-surface-2 px-3 text-base font-bold lg:hidden"
          aria-expanded={open}
          aria-controls={panelId}
          onClick={() => setOpen((v) => !v)}
        >
          <svg aria-hidden="true" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            {open ? <path d="M6 6l12 12M18 6L6 18" /> : <path d="M4 7h16M4 12h16M4 17h16" />}
          </svg>
          Menu
        </button>
      </div>

      <div id={panelId} className={clsx("flex-1 flex-col px-3 pb-4 lg:flex", open ? "flex" : "hidden")}>
        <nav aria-label="Principal">
          <ul className="flex flex-col gap-1">
            {NAV_ITEMS.map((item) => {
              const active = isActive(pathname, item);
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    aria-current={active ? "page" : undefined}
                    className={clsx(
                      "relative flex min-h-11 items-center rounded-lg px-4 py-2 text-base no-underline",
                      active ? "bg-surface-3 font-bold text-fg" : "text-muted hover:bg-surface-2 hover:text-fg",
                    )}
                  >
                    {active && <span aria-hidden="true" className="absolute inset-y-2 left-0 w-1 rounded-full bg-accent-bg" />}
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        <div className="mt-4 flex flex-col gap-3 border-t border-line-soft pt-4 lg:mt-auto">
          <Link
            href="/admin"
            aria-current={adminActive ? "page" : undefined}
            className={clsx(
              "flex min-h-11 items-center gap-2 rounded-lg border px-4 py-2 text-base no-underline",
              adminActive ? "border-gold text-gold" : "border-line text-muted hover:bg-surface-2 hover:text-fg",
            )}
          >
            <LockIcon />
            Administrador
          </Link>
          <ThemeSelect />
        </div>
      </div>
    </header>
  );
}
