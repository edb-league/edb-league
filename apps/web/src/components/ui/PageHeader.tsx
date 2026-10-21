import Image from "next/image";
import type { ReactNode } from "react";
import { num } from "@/lib/format";

export type ArtName = "home" | "rankings" | "matches" | "duel" | "trophy" | "medals" | "xp";

/**
 * Cabeçalho de página. A arte é decorativa (alt vazio) e fica atrás de uma camada
 * sólida sob o texto, então o contraste depende só dos tokens e não da imagem.
 */
export function PageHeader({
  title,
  subtitle,
  art,
  counts,
  children,
}: {
  title: string;
  subtitle: string;
  art?: ArtName;
  counts?: { players: number; matches: number; maps: number };
  /** Faixa inferior do banner (barra de temporada). */
  children?: ReactNode;
}) {
  return (
    <header className="relative isolate overflow-hidden rounded-[var(--radius-card)] border border-t-4 border-line-soft border-t-gold-bg bg-surface-2">
      {art && (
        <>
          <Image
            src={`/art/${art}.webp`}
            alt=""
            fill
            priority
            sizes="(min-width: 1024px) 70vw, 100vw"
            className="-z-20 object-cover object-right"
          />
          <div aria-hidden="true" className="absolute inset-0 -z-10 bg-surface-2/92 md:hidden" />
          <div
            aria-hidden="true"
            className="absolute inset-0 -z-10 hidden bg-linear-to-r from-surface-2 from-40% via-surface-2/85 via-60% to-transparent md:block"
          />
        </>
      )}
      <div className="flex flex-wrap items-end justify-between gap-x-6 gap-y-3 px-5 py-5 md:px-8 md:py-6">
        <div className="max-w-2xl">
          <p className="kicker mb-1">EDB LEAGUE · CS2</p>
          <h1 className="text-4xl leading-none md:text-5xl">{title}</h1>
          <p className="mt-2 max-w-prose text-lg text-muted">{subtitle}</p>
        </div>
        {counts && (
          <ul className="hidden flex-wrap gap-2 md:flex" aria-label="Resumo da liga">
            {(
              [
                ["Jogadores", counts.players],
                ["Partidas", counts.matches],
                ["Mapas", counts.maps],
              ] as const
            ).map(([label, value]) => (
              <li
                key={label}
                className="rounded-full border border-line-soft bg-surface/90 px-3 py-0.5 text-base text-muted"
              >
                <b className="num mr-1 text-lg text-gold">{num(value)}</b>
                {label}
              </li>
            ))}
          </ul>
        )}
      </div>
      {children && <div className="border-t border-line-soft bg-surface/92 px-5 py-2 md:px-8">{children}</div>}
    </header>
  );
}
