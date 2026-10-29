import clsx from "clsx";
import type { ReactNode } from "react";
import { Icon } from "@/components/ui/Icon";

const styles = {
  info: { border: "border-accent", icon: "info", label: "Informação" },
  success: { border: "border-win", icon: "check", label: "Sucesso" },
  warning: { border: "border-gold", icon: "alert", label: "Atenção" },
  error: { border: "border-loss", icon: "x", label: "Erro" },
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
      className={clsx("flex gap-3 rounded-lg border bg-surface-2 p-4 text-base", s.border, className)}
    >
      <Icon name={s.icon} className="mt-1 text-lg" />
      <div>
        <span className="sr-only">{s.label}: </span>
        {title && <p className="font-bold">{title}</p>}
        <div className="text-muted">{children}</div>
      </div>
    </div>
  );
}
