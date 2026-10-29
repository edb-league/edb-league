"use client";

import clsx from "clsx";
import { useEffect, useState } from "react";

/**
 * Índice do Regulamento. Em telas largas fica fixo ao lado e destaca a seção que está na tela;
 * em telas estreitas vira uma fileira de botões. Sem JavaScript continua sendo uma lista de âncoras.
 */
export function TocNav({ sections }: { sections: readonly (readonly [string, string])[] }) {
  const [current, setCurrent] = useState<string | null>(null);

  useEffect(() => {
    const targets = sections.map(([id]) => document.getElementById(id)).filter((el): el is HTMLElement => el !== null);
    if (targets.length === 0) return;
    // A seção "atual" é a última cujo topo já passou de um quinto da altura da tela.
    const update = () => {
      const line = window.innerHeight * 0.25;
      let active: string | null = null;
      for (const el of targets) if (el.getBoundingClientRect().top <= line) active = el.id;
      setCurrent(active);
    };
    update();
    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    return () => {
      window.removeEventListener("scroll", update);
      window.removeEventListener("resize", update);
    };
  }, [sections]);

  return (
    <nav aria-label="Neste regulamento" className="xl:sticky xl:top-24">
      <p className="mb-2 text-base font-bold text-muted">Neste regulamento</p>
      <ol className="flex flex-wrap gap-1 xl:flex-col xl:flex-nowrap xl:gap-0 xl:border-l-2 xl:border-line-soft">
        {sections.map(([id, label]) => {
          const active = current === id;
          return (
            <li key={id}>
              <a
                href={`#${id}`}
                aria-current={active ? "location" : undefined}
                className={clsx(
                  "press flex min-h-11 items-center rounded-lg border px-3.5 text-lg no-underline xl:-ml-0.5 xl:rounded-none xl:border-0 xl:border-l-[3px]",
                  active
                    ? "border-gold-bg font-bold text-fg xl:border-gold-bg"
                    : "border-line-soft text-muted hover:text-fg xl:border-transparent xl:hover:border-line",
                )}
              >
                {label}
              </a>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
