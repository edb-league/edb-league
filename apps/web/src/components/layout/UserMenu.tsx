"use client";

import clsx from "clsx";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useId, useRef, useState } from "react";
import { Avatar } from "@/components/ui/Avatar";
import { sendJson } from "@/lib/client";
import type { Me } from "@/lib/types";

/** Botão "Entrar com Steam": link comum (navegação completa), porque o login passa pelo servidor e pela Steam. */
export function SteamLogin({ className }: { className?: string }) {
  const pathname = usePathname();
  const next = pathname.startsWith("/admin") ? "/admin" : pathname;
  return (
    <a href={`/api/auth/steam/login?next=${encodeURIComponent(next)}`} className={clsx("btn btn-gold w-fit", className)}>
      <svg aria-hidden="true" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="8" r="4" />
        <path d="M4 21c0-4.4 3.6-7 8-7s8 2.6 8 7" />
      </svg>
      Entrar com Steam
    </a>
  );
}

/** Foto e nome de quem está logado, com Meu perfil, Administração (só para o admin) e Sair. */
export function UserMenu({ me }: { me: Me }) {
  const router = useRouter();
  const pathname = usePathname();
  const id = useId();
  const root = useRef<HTMLDivElement>(null);
  const [openOn, setOpenOn] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const open = openOn === pathname;
  const name = me.player?.nickname ?? "Administrador";

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setOpenOn(null);
        root.current?.querySelector<HTMLButtonElement>("button[aria-expanded]")?.focus();
      }
    };
    const onPointer = (event: MouseEvent) => {
      if (!root.current?.contains(event.target as Node)) setOpenOn(null);
    };
    window.addEventListener("keydown", onKey);
    window.addEventListener("mousedown", onPointer);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("mousedown", onPointer);
    };
  }, [open]);

  async function logout() {
    setBusy(true);
    try {
      await sendJson("POST", "/auth/logout");
    } finally {
      setBusy(false);
      setOpenOn(null);
      if (pathname.startsWith("/admin")) router.push("/");
      router.refresh();
    }
  }

  const item = "press flex min-h-11 w-full items-center rounded-lg px-3 text-left text-lg no-underline transition-colors duration-150 hover:bg-surface-2";

  return (
    <div ref={root} className="relative w-full xl:w-auto">
      <button
        type="button"
        aria-expanded={open}
        aria-controls={id}
        onClick={() => setOpenOn(open ? null : pathname)}
        className="btn btn-secondary w-full justify-start gap-2.5 pr-3 pl-1.5 xl:w-auto"
      >
        <Avatar name={name} src={me.avatar} size={32} level={null} decorative className="border-2" />
        <span className="max-w-32 truncate">{name}</span>
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
          className={clsx("ml-auto transition-transform duration-200 ease-[cubic-bezier(0.23,1,0.32,1)]", open && "rotate-180")}
        >
          <path d="M6 9l6 6 6-6" />
        </svg>
      </button>
      <ul
        id={id}
        className={clsx(
          "absolute right-0 z-50 mt-1 flex min-w-56 origin-top-right flex-col rounded-xl border border-line-soft bg-surface p-1.5 shadow-card",
          "transition-[opacity,transform,visibility] duration-150 ease-[cubic-bezier(0.23,1,0.32,1)]",
          open ? "visible scale-100 opacity-100" : "pointer-events-none invisible -translate-y-1 scale-[0.97] opacity-0",
        )}
      >
        {me.player && (
          <li>
            <Link href={`/jogadores/${encodeURIComponent(me.player.id)}`} className={item}>
              Meu perfil
            </Link>
          </li>
        )}
        <li>
          <Link href="/privacidade" className={item}>
            Privacidade
          </Link>
        </li>
        {me.is_admin && (
          <li>
            <Link href="/admin" className={item}>
              Administração
            </Link>
          </li>
        )}
        <li>
          <button type="button" onClick={logout} disabled={busy} className={clsx(item, "text-muted disabled:opacity-60")}>
            {busy ? "Saindo..." : "Sair"}
          </button>
        </li>
      </ul>
    </div>
  );
}
