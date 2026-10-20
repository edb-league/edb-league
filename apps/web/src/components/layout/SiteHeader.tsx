"use client";

import clsx from "clsx";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useId, useRef, useState } from "react";
import { NAV_ITEMS, isActive, type NavItem } from "@/lib/nav";
import { ThemeSelect } from "./ThemeSelect";

function LockIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="5" y="10" width="14" height="11" rx="2" />
      <path d="M8 10V7a4 4 0 0 1 8 0v3" />
    </svg>
  );
}

const itemClass = (active: boolean) =>
  clsx(
    "flex min-h-11 items-center border-b-[3px] px-3 text-lg no-underline xl:min-h-[4.5rem]",
    active
      ? "border-gold-bg font-bold text-fg"
      : "border-transparent font-medium text-muted hover:text-fg xl:hover:border-line-soft",
  );

function NavLink({ item, pathname }: { item: NavItem; pathname: string }) {
  const active = isActive(pathname, item);
  return (
    <Link href={item.href} aria-current={active ? "page" : undefined} className={itemClass(active)}>
      {item.label}
    </Link>
  );
}

/**
 * Menu superior. Em telas largas os itens principais ficam na barra e os demais em "Mais";
 * em telas estreitas tudo vira uma lista aberta pelo botão "Menu" (aria-expanded).
 * Existe um único landmark <nav>.
 */
export function SiteHeader() {
  const pathname = usePathname();
  // Os painéis abertos ficam atrelados à rota em que foram abertos: ao navegar, fecham sozinhos.
  const [openOn, setOpenOn] = useState<string | null>(null);
  const [moreOn, setMoreOn] = useState<string | null>(null);
  const open = openOn === pathname;
  const moreOpen = moreOn === pathname;
  const panelId = useId();
  const moreId = useId();
  const moreButton = useRef<HTMLButtonElement>(null);
  const moreWrap = useRef<HTMLLIElement>(null);

  useEffect(() => {
    if (!open && !moreOpen) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      if (moreOpen) moreButton.current?.focus();
      setOpenOn(null);
      setMoreOn(null);
    };
    const onPointer = (event: MouseEvent) => {
      if (moreOpen && !moreWrap.current?.contains(event.target as Node)) setMoreOn(null);
    };
    window.addEventListener("keydown", onKey);
    window.addEventListener("mousedown", onPointer);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("mousedown", onPointer);
    };
  }, [open, moreOpen]);

  const primary = NAV_ITEMS.filter((i) => i.primary);
  const secondary = NAV_ITEMS.filter((i) => !i.primary);
  const moreActive = secondary.some((i) => isActive(pathname, i));
  const adminActive = pathname.startsWith("/admin");

  return (
    <header className="sticky top-0 z-40 border-b border-line-soft bg-surface">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-6 px-4 md:px-8 xl:flex-nowrap">
        <div className="flex min-h-[4.5rem] flex-1 items-center justify-between gap-3 xl:flex-none">
          <Link href="/" className="flex items-center gap-3 rounded-lg text-fg no-underline" aria-label="EDB LEAGUE, página inicial">
            <Image src="/crest.webp" alt="" width={44} height={44} priority className="size-11 object-contain" />
            <span className="font-display text-3xl font-bold tracking-wider uppercase">EDB League</span>
          </Link>
          <button
            type="button"
            className="inline-flex min-h-11 items-center gap-2 rounded-lg border border-line bg-surface-2 px-3 text-base font-bold xl:hidden"
            aria-expanded={open}
            aria-controls={panelId}
            onClick={() => setOpenOn(open ? null : pathname)}
          >
            <svg aria-hidden="true" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              {open ? <path d="M6 6l12 12M18 6L6 18" /> : <path d="M4 7h16M4 12h16M4 17h16" />}
            </svg>
            Menu
          </button>
        </div>

        <div id={panelId} className={clsx("w-full flex-1 flex-col gap-3 pb-4 xl:flex xl:w-auto xl:flex-row xl:flex-nowrap xl:items-center xl:gap-4 xl:pb-0", open ? "flex" : "hidden")}>
          <nav aria-label="Principal" className="xl:flex-1 xl:min-w-0">
            <ul className="flex flex-col xl:flex-row xl:gap-1">
              {primary.map((item) => (
                <li key={item.href}>
                  <NavLink item={item} pathname={pathname} />
                </li>
              ))}
              <li ref={moreWrap} className="relative">
                <button
                  ref={moreButton}
                  type="button"
                  aria-expanded={moreOpen}
                  aria-controls={moreId}
                  onClick={() => setMoreOn(moreOpen ? null : pathname)}
                  className={clsx(itemClass(moreActive), "hidden xl:flex xl:gap-1.5")}
                >
                  Mais
                  <svg aria-hidden="true" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d={moreOpen ? "M6 15l6-6 6 6" : "M6 9l6 6 6-6"} />
                  </svg>
                </button>
                <ul
                  id={moreId}
                  className={clsx(
                    "flex flex-col xl:absolute xl:top-full xl:right-0 xl:z-50 xl:min-w-56 xl:rounded-xl xl:border xl:border-line-soft xl:bg-surface xl:p-1.5 xl:shadow-card",
                    moreOpen ? "xl:flex" : "xl:hidden",
                  )}
                >
                  {secondary.map((item) => {
                    const active = isActive(pathname, item);
                    return (
                      <li key={item.href}>
                        <Link
                          href={item.href}
                          aria-current={active ? "page" : undefined}
                          className={clsx(
                            "flex min-h-11 items-center rounded-lg px-3.5 text-lg no-underline xl:hover:bg-surface-2",
                            active ? "font-bold text-fg" : "text-muted hover:text-fg",
                          )}
                        >
                          {item.label}
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              </li>
            </ul>
          </nav>

          <div className="flex flex-wrap items-center gap-3 xl:flex-nowrap">
            <ThemeSelect />
            <Link
              href="/admin"
              aria-current={adminActive ? "page" : undefined}
              className="inline-flex min-h-11 items-center gap-2 rounded-lg bg-gold-bg px-4 text-base font-bold text-on-gold no-underline hover:brightness-110"
            >
              <LockIcon />
              Administrador
            </Link>
          </div>
        </div>
      </div>
    </header>
  );
}
