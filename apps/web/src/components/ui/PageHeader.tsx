import Image from "next/image";
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
}: {
  title: string;
  subtitle: string;
  art?: ArtName;
  counts?: { players: number; matches: number; maps: number };
}) {
  return (
    <header className="relative isolate overflow-hidden rounded-[var(--radius-card)] border border-line-soft bg-surface-2">
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
      <div className="max-w-2xl px-5 py-7 md:px-8 md:py-10">
        <p className="kicker mb-2">EDB LEAGUE · CS2</p>
        <h1 className="text-3xl font-extrabold md:text-4xl">{title}</h1>
        <p className="mt-3 max-w-prose text-lg text-muted">{subtitle}</p>
        {counts && (
          <ul className="mt-5 flex flex-wrap gap-2" aria-label="Resumo da liga">
            {(
              [
                ["Jogadores", counts.players],
                ["Partidas", counts.matches],
                ["Mapas", counts.maps],
              ] as const
            ).map(([label, value]) => (
              <li
                key={label}
                className="rounded-full border border-line bg-surface/90 px-3 py-1 text-sm text-muted"
              >
                <b className="tabular mr-1 text-gold">{num(value)}</b>
                {label}
              </li>
            ))}
          </ul>
        )}
      </div>
    </header>
  );
}
