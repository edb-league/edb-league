"use client";

import { usePathname, useSearchParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";

/**
 * Fio dourado no topo durante a navegação entre páginas. A página trabalha no servidor, então o
 * clique num link pode levar alguns segundos (a API hiberna no plano gratuito); sem isso o site
 * parece travado. Só aparece depois de 120 ms, para não piscar em navegações rápidas.
 */
export function NavProgress() {
  const pathname = usePathname();
  const search = useSearchParams().toString();
  const route = `${pathname}?${search}`;
  const [phase, setPhase] = useState<"idle" | "loading" | "done">("idle");
  const startedOn = useRef(route);
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  // Enquanto a página nova não chega, o conteúdo antigo fica esmaecido (via atributo no <html>).
  // Nada disso existe sem JavaScript, então o site continua inteiro nesse caso.
  useEffect(() => {
    document.documentElement.toggleAttribute("data-navigating", phase === "loading");
    return () => document.documentElement.removeAttribute("data-navigating");
  }, [phase]);

  useEffect(() => {
    const onClick = (event: MouseEvent) => {
      if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      const link = (event.target as Element | null)?.closest("a");
      if (!link || link.target === "_blank" || link.hasAttribute("download")) return;
      const url = new URL(link.href, window.location.href);
      if (url.origin !== window.location.origin) return;
      if (url.pathname === window.location.pathname && url.search === window.location.search) return; // só âncora
      startedOn.current = route;
      clearTimeout(timer.current);
      timer.current = setTimeout(() => setPhase("loading"), 120);
    };
    document.addEventListener("click", onClick);
    return () => document.removeEventListener("click", onClick);
  }, [route]);

  // A rota mudou: completa a barra e some.
  useEffect(() => {
    if (startedOn.current === route) return;
    clearTimeout(timer.current);
    startedOn.current = route;
    const finish = setTimeout(() => setPhase("done"), 0);
    const hide = setTimeout(() => setPhase("idle"), 300);
    return () => {
      clearTimeout(finish);
      clearTimeout(hide);
    };
  }, [route]);

  if (phase === "idle") return null;
  return (
    <div aria-hidden="true" className="pointer-events-none fixed inset-x-0 top-0 z-50 h-[3px]">
      <div className={phase === "done" ? "nav-progress-done h-full bg-gold-bg" : "nav-progress h-full bg-gold-bg"} />
    </div>
  );
}
