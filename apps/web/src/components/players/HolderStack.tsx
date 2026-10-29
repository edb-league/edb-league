import Link from "next/link";
import { Avatar } from "@/components/ui/Avatar";
import type { PlayerRef } from "@/lib/types";

/**
 * Fotos sobrepostas de quem tem a conquista (só visuais) e, ao lado, os dois primeiros nomes como
 * links. Os nomes ficam em texto corrido, que tem alvo de clique normal; as fotos não são links
 * porque, sobrepostas, os alvos ficariam menores que o mínimo de 24 px.
 */
export function HolderStack({
  holders,
  avatars,
  max = 5,
}: {
  holders: PlayerRef[];
  avatars: Record<string, string>;
  max?: number;
}) {
  if (holders.length === 0) return null;
  const shown = holders.slice(0, max);
  const rest = holders.length - shown.length;
  const named = holders.slice(0, 2);
  const more = holders.length - named.length;
  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5">
      <ul aria-hidden="true" className="flex -space-x-2">
        {shown.map((h) => (
          <li key={h.id} title={h.name} className="rounded-full ring-2 ring-surface">
            <Avatar name={h.name} src={avatars[h.id]} size={32} decorative className="border-2" />
          </li>
        ))}
        {rest > 0 && (
          <li className="num inline-flex size-8 items-center justify-center rounded-full bg-surface-3 text-sm ring-2 ring-surface">
            +{rest}
          </li>
        )}
      </ul>
      <p className="min-w-0 text-sm text-muted">
        {named.map((h, i) => (
          <span key={h.id}>
            {i > 0 && ", "}
            <Link href={`/jogadores/${encodeURIComponent(h.id)}`}>{h.name}</Link>
          </span>
        ))}
        {more > 0 && ` e mais ${more}`}
      </p>
    </div>
  );
}
