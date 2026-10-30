import { expect, test } from "@playwright/test";
import { expectNoViolations, ids, loginAsAdmin } from "./helpers";

const STATIC_ROUTES = [
  "/",
  "/rankings/elite",
  "/rankings/superacao",
  "/rankings/xp",
  "/rankings/bagres",
  "/missoes-xp",
  "/sorteador",
  "/regulamento",
  "/partidas",
  "/jogadores",
  "/hall-da-fama",
  "/temporadas",
  "/privacidade",
  "/medalhas",
  "/admin",
];

for (const scheme of ["light", "dark"] as const) {
  test.describe(`axe, tema ${scheme}`, () => {
    test.use({ colorScheme: scheme });

    for (const route of STATIC_ROUTES) {
      test(route, async ({ page }) => {
        await page.goto(route);
        await expect(page.getByRole("heading", { level: 1 })).toHaveCount(1);
        await expectNoViolations(page, `${route} (${scheme})`);
      });
    }

    test("rotas dinâmicas", async ({ page, request }) => {
      const { playerA, playerB, mapId, seriesId } = await ids(request);
      for (const route of [
        `/jogadores/${playerA}`,
        `/jogadores/${playerA}?aba=estatisticas`,
        `/jogadores/${playerA}?aba=estatisticas&lado=t`,
        `/jogadores/${playerA}?aba=estatisticas&vista=weapons`,
        `/jogadores/${playerA}?aba=estatisticas&vista=opponents`,
        `/jogadores/${playerA}?aba=partidas`,
        `/jogadores/${playerA}?aba=medalhas`,
        `/medalhas?faixa=gold`,
        `/partidas/mapa/${mapId}`,
        `/partidas?confronto=${seriesId}`,
        `/comparar`,
        `/comparar?a=${playerA}&b=${playerB}`,
      ]) {
        await page.goto(route);
        await expect(page.getByRole("heading", { level: 1 })).toHaveCount(1);
        await expectNoViolations(page, `${route} (${scheme})`);
      }
    });

    test("administração autenticada, todas as abas", async ({ page }) => {
      await loginAsAdmin(page);
      for (const tab of ["Elenco", "Importar", "Importar série", "Confrontos", "Temporadas", "Exportar"]) {
        await page.getByRole("tab", { name: tab, exact: true }).click();
        await expectNoViolations(page, `/admin aba ${tab} (${scheme})`);
      }
    });
  });
}

test("tema escolhido manualmente persiste e continua acessível", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Tema").selectOption("dark");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await expectNoViolations(page, "home com tema escuro manual");
});
