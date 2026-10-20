import clsx from "clsx";
import type { ReactNode } from "react";

/** Use dentro de <dl>. O rótulo vem antes do valor, como a leitura de tela espera. */
export function Stat({
  label,
  value,
  hint,
  className,
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  className?: string;
}) {
  return (
    <div className={clsx("rounded-lg border border-line-soft bg-surface-2 px-4 py-3", className)}>
      <dt className="text-sm text-muted">{label}</dt>
      <dd className="tabular text-2xl font-bold">{value}</dd>
      {hint && <dd className="text-sm text-subtle">{hint}</dd>}
    </div>
  );
}

export function StatGrid({ children, className }: { children: ReactNode; className?: string }) {
  return <dl className={clsx("grid grid-cols-2 gap-3 md:grid-cols-4", className)}>{children}</dl>;
}
