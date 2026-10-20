import clsx from "clsx";
import Link from "next/link";
import { ACHIEVEMENT_TABS } from "@/lib/nav";

/** Barra de abas da área Conquistas: as mesmas três páginas do grupo do menu. */
export function AchievementTabs({ current }: { current: string }) {
  return (
    <nav aria-label="Conquistas">
      <ul className="flex flex-wrap gap-2">
        {ACHIEVEMENT_TABS.map((tab) => {
          const active = tab.href === current;
          return (
            <li key={tab.href}>
              <Link
                href={tab.href}
                aria-current={active ? "page" : undefined}
                className={clsx(
                  "inline-flex min-h-11 items-center rounded-lg border px-5 text-base font-bold no-underline",
                  active ? "border-gold-bg bg-gold-bg text-on-gold" : "border-line bg-surface text-fg hover:bg-surface-2",
                )}
              >
                {tab.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
