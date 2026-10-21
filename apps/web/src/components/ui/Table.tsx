import clsx from "clsx";
import type { ComponentProps, ReactNode } from "react";

/**
 * Tabela com rolagem horizontal acessível: a região é focável (teclado), tem nome
 * e a <caption> descreve o conteúdo para leitores de tela.
 */
export function TableWrap({
  caption,
  children,
  className,
}: {
  caption: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      role="region"
      aria-label={caption}
      tabIndex={0}
      className={clsx("relative overflow-x-auto rounded-lg border border-line-soft bg-surface", className)}
    >
      <table className="w-full text-base">
        <caption className="sr-only">{caption}</caption>
        {children}
      </table>
    </div>
  );
}

export function Th({
  numeric,
  className,
  scope = "col",
  ...props
}: ComponentProps<"th"> & { numeric?: boolean }) {
  return (
    <th
      scope={scope}
      className={clsx(
        "bg-surface-2 px-3 py-2.5 text-sm font-bold whitespace-nowrap text-muted",
        numeric ? "text-right" : "text-left",
        className,
      )}
      {...props}
    />
  );
}

export function Td({ numeric, className, ...props }: ComponentProps<"td"> & { numeric?: boolean }) {
  return (
    <td
      className={clsx("border-t border-line-soft px-3 py-2.5", numeric && "tabular text-right", className)}
      {...props}
    />
  );
}
