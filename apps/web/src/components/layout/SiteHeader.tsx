"use client";

import clsx from "clsx";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useId, useRef, useState } from "react";
import { NAV, isActive, isGroup, type NavGroup, type NavLink } from "@/lib/nav";
import type { Me } from "@/lib/types";
import { SteamLogin, UserMenu } from "./UserMenu";

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
    "flex min-h-11 items-center border-b-[3px] px-3 text-lg no-underline transition-colors duration-150 xl:min-h-[4.5rem] xl:px-2.5",
    active
      ? "border-gold-bg font-bold text-fg"
      : "border-transparent font-medium text-muted hover:text-fg xl:hover:border-line-soft",
  );

function Group({
  group,
  pathname,
  open,
  onToggle,
}: {
  group: NavGroup;
  pathname: string;
  open: boolean;
  onToggle: () => void;
}) {
  const id = useId();
  const active = group.items.some((i) => isActive(pathname, i));
  return (
    <li data-group className="relative">
      <button
        type="button"
        aria-expanded={open}
        aria-controls={id}
        onClick={onToggle}
        className={clsx(itemClass(active), "hidden w-full xl:flex xl:gap-1.5")}
      >
        {group.label}
        <svg
          aria-hidden="true"
          viewBox="0 0 24 24"
          width="16"
          height="16"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          className={clsx("transition-transform duration-200 ease-[cubic-bezier(0.23,1,0.32,1)]", open && "rotate-180")}
        >
          <path d="M6 9l6 6 6-6" />
        </svg>
      </button>
      {/* No menu aberto do celular o grupo é só um título acima da sua lista. */}
      <p className="px-3 pt-3 pb-1 text-base font-bold text-muted xl:hidden">{group.label}</p>
      <ul
        id={id}
        className={clsx(
          "flex flex-col xl:absolute xl:top-full xl:left-0 xl:z-50 xl:min-w-60 xl:origin-top-left xl:rounded-xl xl:border xl:border-line-soft xl:bg-surface xl:p-1.5 xl:shadow-card",
          // Fechado fica invisível (some do teclado e dos leitores de tela) e abre a partir do botão.
          "xl:transition-[opacity,transform,visibility] xl:duration-150 xl:ease-[cubic-bezier(0.23,1,0.32,1)]",
          open ? "xl:visible xl:scale-100 xl:opacity-100" : "xl:pointer-events-none xl:invisible xl:-translate-y-1 xl:scale-[0.97] xl:opacity-0",
        )}
      >
        {group.items.map((item) => {
          const current = isActive(pathname, item);
          return (
            <li key={item.href}>
              <Link
                href={item.href}
                aria-current={current ? "page" : undefined}
                className={clsx(
                  "flex min-h-11 items-center rounded-lg px-3 text-lg no-underline transition-colors duration-150 xl:hover:bg-surface-2",
                  current ? "font-bold text-fg" : "text-muted hover:text-fg",
                )}
              >
                {item.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </li>
  );
}

function DirectLink({ item, pathname }: { item: NavLink; pathname: string }) {
  const active = isActive(pathname, item);
  return (
    <li>
      <Link href={item.href} aria-current={active ? "page" : undefined} className={itemClass(active)}>
        {item.label}
      </Link>
    </li>
  );
}

/**
 * Menu superior. Em telas largas há itens diretos e dois grupos (Conquistas e Ferramentas) com
 * lista suspensa; em telas estreitas tudo vira uma lista aberta pelo botão "Menu" (aria-expanded).
 * Existe um único landmark <nav> principal.
 */
export function SiteHeader({ me }: { me: Me }) {
  const pathname = usePathname();
  // Os painéis abertos ficam atrelados à rota em que foram abertos: ao navegar, fecham sozinhos.
  const [openOn, setOpenOn] = useState<string | null>(null);
  const [groupOn, setGroupOn] = useState<{ path: string; label: string } | null>(null);
  const open = openOn === pathname;
  const openGroup = groupOn?.path === pathname ? groupOn.label : null;
  const panelId = useId();
  const navRef = useRef<HTMLUListElement>(null);

  useEffect(() => {
    if (!open && !openGroup) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      if (openGroup) navRef.current?.querySelector<HTMLButtonElement>('button[aria-expanded="true"]')?.focus();
      setOpenOn(null);
      setGroupOn(null);
    };
    const onPointer = (event: MouseEvent) => {
      const inside = (event.target as Element | null)?.closest("[data-group]");
      if (openGroup && !inside) setGroupOn(null);
    };
    window.addEventListener("keydown", onKey);
    window.addEventListener("mousedown", onPointer);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("mousedown", onPointer);
    };
  }, [open, openGroup]);

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
            className="btn btn-secondary xl:hidden"
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

        <div
          id={panelId}
          className={clsx(
            "w-full flex-1 flex-col gap-3 pb-4 xl:flex xl:w-auto xl:flex-row xl:flex-nowrap xl:items-center xl:gap-4 xl:pb-0",
            open ? "reveal flex" : "hidden",
          )}
        >
          <nav aria-label="Principal" className="xl:min-w-0 xl:flex-1">
            <ul ref={navRef} className="flex flex-col xl:flex-row xl:gap-0.5">
              {NAV.map((entry) =>
                isGroup(entry) ? (
                  <Group
                    key={entry.label}
                    group={entry}
                    pathname={pathname}
                    open={openGroup === entry.label}
                    onToggle={() =>
                      setGroupOn(openGroup === entry.label ? null : { path: pathname, label: entry.label })
                    }
                  />
                ) : (
                  <DirectLink key={entry.href} item={entry} pathname={pathname} />
                ),
              )}
            </ul>
          </nav>

          {me.authenticated ? (
            <UserMenu me={me} />
          ) : me.login_enabled ? (
            <SteamLogin />
          ) : (
            <Link
              href="/admin"
              aria-current={adminActive ? "page" : undefined}
              className="btn btn-gold w-fit"
            >
              <LockIcon />
              Administrador
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
