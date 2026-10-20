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
    <div className={clsx("card px-4 py-4", className)}>
      <dt className="mb-1 text-base font-semibold text-muted">{label}</dt>
      <dd className="num text-4xl leading-none">{value}</dd>
      {hint && <dd className="mt-1 text-base text-muted">{hint}</dd>}
    </div>
  );
}

export function StatGrid({ children, className }: { children: ReactNode; className?: string }) {
  return <dl className={clsx("grid grid-cols-2 gap-3 md:grid-cols-4", className)}>{children}</dl>;
}
