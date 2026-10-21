import clsx from "clsx";
import type { ReactNode } from "react";

const styles = {
  info: { border: "border-accent", icon: "ℹ", label: "Informação" },
  success: { border: "border-win", icon: "✓", label: "Sucesso" },
  warning: { border: "border-gold", icon: "!", label: "Atenção" },
  error: { border: "border-loss", icon: "✕", label: "Erro" },
} as const;

export function Notice({
  tone = "info",
  title,
  children,
  className,
}: {
  tone?: keyof typeof styles;
  title?: string;
  children: ReactNode;
  className?: string;
}) {
  const s = styles[tone];
  return (
    <div
      role={tone === "error" ? "alert" : "status"}
      className={clsx("flex gap-3 rounded-lg border-l-4 bg-surface-2 p-4 text-base", s.border, className)}
    >
      <span aria-hidden="true" className="mt-0.5 font-bold">
        {s.icon}
      </span>
      <div>
        <span className="sr-only">{s.label}: </span>
        {title && <p className="font-bold">{title}</p>}
        <div className="text-muted">{children}</div>
      </div>
    </div>
  );
}
