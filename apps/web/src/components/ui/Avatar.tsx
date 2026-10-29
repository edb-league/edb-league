import clsx from "clsx";
import Image from "next/image";
import { LevelBadge } from "@/components/ui/LevelBadge";

function initials(name: string): string {
  const parts = name.replace(/[()]/g, " ").trim().split(/\s+/).filter(Boolean);
  const head = parts[0];
  const tail = parts[parts.length - 1];
  if (!head || !tail) return "?";
  if (parts.length === 1) return head.slice(0, 2).toUpperCase();
  return ((head[0] ?? "") + (tail[0] ?? "")).toUpperCase();
}

/**
 * Foto da Steam, ou um monograma (iniciais sobre degradê azul com aro dourado) quando não há foto.
 * O nome do jogador sempre aparece ao lado, então o monograma é decorativo.
 */
export function Avatar({
  name,
  src,
  size = 96,
  className,
  level,
  decorative,
}: {
  name: string;
  src?: string | null;
  size?: number;
  className?: string;
  /** Selo de nível no canto inferior direito (como nos perfis do FACEIT). */
  level?: number | null;
  /** Em listas, onde o nome já está ao lado: a imagem não é lida por leitores de tela. */
  decorative?: boolean;
}) {
  const face = <AvatarFace name={name} src={src} size={size} className={className} decorative={decorative} />;
  if (level === undefined || level === null) return face;
  return (
    <span className="relative inline-flex shrink-0">
      {face}
      <LevelBadge
        level={level}
        size={size >= 56 ? "sm" : "xs"}
        className={size >= 56 ? "absolute -right-1.5 -bottom-1.5 ring-2 ring-surface" : "absolute -right-1 -bottom-1 rounded-md! ring-2 ring-surface"}
      />
    </span>
  );
}

function AvatarFace({
  name,
  src,
  size,
  className,
  decorative,
}: {
  name: string;
  src?: string | null;
  size: number;
  className?: string;
  decorative?: boolean;
}) {
  const box = { width: size, height: size };
  if (src) {
    return (
      <Image
        src={src}
        alt={decorative ? "" : `Foto de ${name}`}
        width={size}
        height={size}
        unoptimized
        className={clsx("rounded-full border-[3px] border-gold-bg object-cover", className)}
        style={box}
      />
    );
  }
  return (
    <span
      role={decorative ? undefined : "img"}
      aria-label={decorative ? undefined : `${name}, sem foto da Steam`}
      aria-hidden={decorative ? true : undefined}
      style={{ ...box, fontSize: size * 0.4 }}
      className={clsx(
        "num inline-flex shrink-0 items-center justify-center rounded-full border-[3px] border-gold-bg bg-linear-to-br from-surface-3 to-surface text-fg",
        className,
      )}
    >
      <span aria-hidden="true">{initials(name)}</span>
    </span>
  );
}
