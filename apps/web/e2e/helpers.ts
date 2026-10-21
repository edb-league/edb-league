import AxeBuilder from "@axe-core/playwright";
import { expect, type APIRequestContext, type Page } from "@playwright/test";

export const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD ?? "demo-senha-123";

export async function ids(request: APIRequestContext) {
  const players = (await (await request.get("/api/players")).json()) as { id: string }[] | { players: { id: string }[] };
  const list = Array.isArray(players) ? players : players.players;
  const matches = (await (await request.get("/api/matches")).json()) as {
    bo3: { id: string; maps: { id: string }[] }[];
  };
  const series = matches.bo3.find((s) => s.maps.length > 0)!;
  return { playerA: list[0].id, playerB: list[1].id, mapId: series.maps[0].id, seriesId: series.id };
}

/** Regras WCAG 2.0, 2.1 e 2.2 níveis A e AA. */
export async function expectNoViolations(page: Page, label: string) {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
    .analyze();
  const summary = results.violations.map((v) => ({
    rule: v.id,
    impact: v.impact,
    nodes: v.nodes.slice(0, 4).map((n) => n.target.join(" ")),
  }));
  expect(summary, `${label}: violações de acessibilidade`).toEqual([]);
}

export async function loginAsAdmin(page: Page) {
  await page.goto("/admin");
  await page.getByLabel("Senha do administrador").fill(ADMIN_PASSWORD);
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page.getByRole("tab", { name: "Elenco" })).toBeVisible();
}
