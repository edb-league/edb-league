"use client";

import * as RadixTabs from "@radix-ui/react-tabs";
import type { ReactNode } from "react";

export type TabItem = { value: string; label: string; content: ReactNode };

/** Abas com navegação por setas, Home/End e papéis ARIA corretos (Radix). */
export function Tabs({ tabs, label, defaultValue }: { tabs: TabItem[]; label: string; defaultValue?: string }) {
  return (
    <RadixTabs.Root defaultValue={defaultValue ?? tabs[0]?.value}>
      <RadixTabs.List aria-label={label} className="mb-4 flex flex-wrap gap-1 border-b border-line-soft">
        {tabs.map((tab) => (
          <RadixTabs.Trigger
            key={tab.value}
            value={tab.value}
            className="-mb-px min-h-11 rounded-t-lg border-b-4 border-transparent px-4 py-2 text-base font-bold text-muted hover:bg-surface-2 hover:text-fg data-[state=active]:border-accent data-[state=active]:text-fg"
          >
            {tab.label}
          </RadixTabs.Trigger>
        ))}
      </RadixTabs.List>
      {tabs.map((tab) => (
        <RadixTabs.Content key={tab.value} value={tab.value} tabIndex={-1} className="focus-visible:outline-none">
          {tab.content}
        </RadixTabs.Content>
      ))}
    </RadixTabs.Root>
  );
}
