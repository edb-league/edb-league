import clsx from "clsx";

export type IconName =
  | "check"
  | "x"
  | "info"
  | "alert"
  | "star"
  | "arrow-right"
  | "arrow-up"
  | "arrow-down"
  | "shuffle"
  | "book"
  | "versus";

const paths: Record<Exclude<IconName, "star">, string> = {
  check: "M5 12.5l4.5 4.5L19 7.5",
  x: "M6 6l12 12M18 6L6 18",
  info: "M12 11v6M12 7.5v.01M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z",
  alert: "M12 8v5M12 16.5v.01M10.3 4.2L2.9 17a2 2 0 0 0 1.7 3h14.8a2 2 0 0 0 1.7-3L13.7 4.2a2 2 0 0 0-3.4 0z",
  "arrow-right": "M5 12h14M13 6l6 6-6 6",
  "arrow-up": "M12 19V5M6 11l6-6 6 6",
  "arrow-down": "M12 5v14M6 13l6 6 6-6",
  shuffle: "M16 4h4v4M4 20 20 4M20 16v4h-4M14.5 14.5 20 20M4 4l5 5",
  book: "M5 4.5A1.5 1.5 0 0 1 6.5 3H19v15H6.5A1.5 1.5 0 0 0 5 19.5zM5 19.5A1.5 1.5 0 0 0 6.5 21H19M9 7.5h6",
  versus: "M7 4v13M3 8l4-4 4 4M17 20V7M13 16l4 4 4-4",
};

/** Ícones de traço único (24x24, currentColor). Decorativos: o texto vizinho carrega o significado. */
export function Icon({ name, className }: { name: IconName; className?: string }) {
  const common = { "aria-hidden": true, "data-arrow": name.startsWith("arrow") ? name.slice(6) : undefined, viewBox: "0 0 24 24", width: "1em", height: "1em", className: clsx("inline-block shrink-0 align-[-0.125em]", name.startsWith("arrow") && "ml-1", className) } as const;
  if (name === "star") {
    return (
      <svg {...common} fill="currentColor">
        <path d="M12 2.6l2.9 6 6.6.9-4.8 4.6 1.2 6.5L12 17.4l-5.9 3.2 1.2-6.5L2.5 9.5l6.6-.9z" />
      </svg>
    );
  }
  return (
    <svg {...common} fill="none" stroke="currentColor" strokeWidth="2.25" strokeLinecap="round" strokeLinejoin="round">
      <path d={paths[name]} />
    </svg>
  );
}

/** Fileira de estrelas decorativa; quem usa informa a quantidade em texto ou aria-label. */
export function StarRow({ count, className }: { count: number; className?: string }) {
  return (
    <span aria-hidden="true" className={clsx("inline-flex gap-0.5", className)}>
      {Array.from({ length: count }, (_, i) => (
        <Icon key={i} name="star" />
      ))}
    </span>
  );
}
