import clsx from "clsx";
import type { ComponentProps, ReactNode } from "react";

export function Card({ className, ...props }: ComponentProps<"section">) {
  return <section className={clsx("card p-4 md:p-6", className)} {...props} />;
}

/** Título de seção com nível de heading explícito. */
export function SectionTitle({
  id,
  title,
  level = 2,
  children,
}: {
  id?: string;
  title: ReactNode;
  level?: 2 | 3;
  children?: ReactNode;
}) {
  const Heading = level === 2 ? "h2" : "h3";
  return (
    <div className="mb-3">
      <Heading id={id} className={clsx(level === 3 && "font-display font-bold uppercase", level === 2 ? "text-3xl md:text-4xl" : "text-2xl")}>
        {title}
      </Heading>
      {children && <p className="mt-1 text-base text-muted">{children}</p>}
    </div>
  );
}

export function EmptyState({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <p
      className={clsx(
        "rounded-lg border border-dashed border-line bg-surface p-6 text-center text-base text-muted",
        className,
      )}
    >
      {children}
    </p>
  );
}
