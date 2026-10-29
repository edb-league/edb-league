import clsx from "clsx";
import type { ReactNode } from "react";
import { Icon } from "@/components/ui/Icon";

const tones = {
  neutral: "text-muted border-line-soft",
  accent: "text-accent border-accent",
  gold: "text-gold border-gold",
  win: "text-win border-win",
  loss: "text-loss border-loss",
  pt: "text-pt border-pt",
  pl: "text-pl border-pl",
} as const;

export type Tone = keyof typeof tones;

export function Badge({ tone = "neutral", children, className }: { tone?: Tone; children: ReactNode; className?: string }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1 rounded-full border bg-surface-2 px-2.5 py-0.5 text-sm font-bold whitespace-nowrap",
        tones[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

/** Marca a linha ou o cartão de quem está logado. */
export function YouBadge({ className }: { className?: string }) {
  return (
    <Badge tone="accent" className={className}>
      Você
    </Badge>
  );
}

/** Resultado sempre com ícone e texto, nunca só cor. */
export function OutcomeBadge({ outcome }: { outcome: "win" | "loss" | "unknown" }) {
  if (outcome === "win")
    return (
      <Badge tone="win">
        <Icon name="check" /> Vitória
      </Badge>
    );
  if (outcome === "loss")
    return (
      <Badge tone="loss">
        <Icon name="x" /> Derrota
      </Badge>
    );
  return (
    <Badge>
      <span aria-hidden="true">–</span> Sem resultado
    </Badge>
  );
}

/** Time PT (vermelho) ou PL (azul): cor e letras. Outros nomes ficam neutros. */
export function TeamTag({ name }: { name: string }) {
  const key = name.trim().toUpperCase();
  const tone: Tone = key === "PT" ? "pt" : key === "PL" ? "pl" : "neutral";
  const shape = key === "PT" ? "●" : key === "PL" ? "◆" : "";
  return (
    <Badge tone={tone}>
      {shape && <span aria-hidden="true">{shape}</span>}
      {name}
    </Badge>
  );
}
