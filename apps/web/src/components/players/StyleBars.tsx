import { num } from "@/lib/format";

export type StyleItem = { label: string; basis: string; score: number | null };

/**
 * Estilo de jogo: posição do jogador entre os da liga (100 = melhor, 0 = pior).
 * O número está sempre em texto; a barra e o traço do meio da liga reforçam.
 */
export function StyleBars({ items }: { items: StyleItem[] }) {
  return (
    <ul className="flex flex-col gap-4">
      {items.map((item) => (
        <li key={item.label}>
          <div className="mb-1.5 flex items-baseline justify-between gap-3">
            <span className="text-lg font-semibold">
              {item.label} <span className="text-base font-normal text-muted">({item.basis})</span>
            </span>
            <b className="num text-3xl leading-none text-gold">
              {item.score === null ? "–" : num(item.score)}
              {item.score !== null && <span className="sr-only"> de 100</span>}
            </b>
          </div>
          <div aria-hidden="true" className="relative h-3 rounded-full bg-surface-3">
            <div className="h-full rounded-full bg-gold-bg" style={{ width: `${item.score ?? 0}%` }} />
            <span className="absolute -top-1 left-1/2 h-5 w-[3px] rounded-sm bg-fg" />
          </div>
        </li>
      ))}
    </ul>
  );
}
