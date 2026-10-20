import { expect, test } from "@playwright/test";
import { ids } from "./helpers";

test("idioma, skip link e landmarks de navegação com nome", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("html")).toHaveAttribute("lang", "pt-BR");
  await page.keyboard.press("Tab");
  const skip = page.getByRole("link", { name: /pular para o conteúdo/i });
  await expect(skip).toBeFocused();
  await expect(skip).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Principal" })).toHaveCount(1);
  for (const nav of await page.locator("nav").all()) {
    await expect(nav, "todo <nav> precisa de nome acessível").toHaveAttribute("aria-label", /.+/);
  }
  await skip.press("Enter");
  await expect(page.locator("main")).toBeFocused();
});

test("item atual do menu usa aria-current", async ({ page }) => {
  await page.goto("/rankings/xp");
  await expect(page.getByRole("link", { name: /rankings/i }).first()).toHaveAttribute("aria-current", "page");
});

test("menu no celular abre, fecha com Esc e expõe aria-expanded", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 800 });
  await page.goto("/");
  const button = page.getByRole("button", { name: /menu/i });
  await expect(button).toHaveAttribute("aria-expanded", "false");
  await button.click();
  await expect(button).toHaveAttribute("aria-expanded", "true");
  await page.keyboard.press("Escape");
  await expect(button).toHaveAttribute("aria-expanded", "false");
});

test("menu fecha ao navegar", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 800 });
  await page.goto("/");
  const button = page.getByRole("button", { name: /menu/i });
  await button.click();
  await page.getByRole("navigation", { name: "Principal" }).getByRole("link", { name: /medalhas/i }).click();
  await expect(page).toHaveURL(/\/medalhas$/);
  await expect(button).toHaveAttribute("aria-expanded", "false");
});

for (const width of [320, 768, 1280]) {
  test(`sem rolagem horizontal na página em ${width}px`, async ({ page, request }) => {
    const { playerA, mapId } = await ids(request);
    await page.setViewportSize({ width, height: 900 });
    for (const route of ["/", "/rankings/elite", "/partidas", `/jogadores/${playerA}`, `/partidas/mapa/${mapId}`, "/admin"]) {
      await page.goto(route);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
      expect(overflow, `${route} em ${width}px`).toBeLessThanOrEqual(0);
    }
  });
}

test("zoom de 200% (viewport equivalente a 640px) mantém o conteúdo legível", async ({ page }) => {
  await page.setViewportSize({ width: 640, height: 450 });
  await page.goto("/rankings/elite");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow).toBeLessThanOrEqual(0);
});

test("movimento reduzido remove transições", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  const duration = await page.evaluate(() => getComputedStyle(document.querySelector("a")!).transitionDuration);
  expect(parseFloat(duration)).toBeLessThan(0.02);
});

test("links antigos do Streamlit redirecionam", async ({ page, request }) => {
  const { playerA } = await ids(request);
  await page.goto("/?page=rankings");
  await expect(page).toHaveURL(/\/rankings\/elite$/);
  await page.goto(`/?player=${playerA}`);
  await expect(page).toHaveURL(new RegExp(`/jogadores/${playerA}$`));
});

test("jogador inexistente mostra página 404 amigável", async ({ page }) => {
  const response = await page.goto("/jogadores/nao-existe");
  expect(response?.status()).toBe(404);
  await expect(page.getByRole("heading", { level: 1 })).toContainText(/não encontrad/i);
});

test("aviso de dados de demonstração é visível", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText(/dados de demonstra/i).first()).toBeVisible();
});

test("comparar funciona sem JavaScript", async ({ browser, request }) => {
  const { playerA, playerB } = await ids(request);
  const context = await browser.newContext({ javaScriptEnabled: false, locale: "pt-BR" });
  const page = await context.newPage();
  await page.goto("/comparar");
  await page.getByLabel("Jogador 1").selectOption(playerA);
  await page.getByLabel("Jogador 2").selectOption(playerB);
  await page.getByRole("button", { name: /comparar/i }).click();
  await expect(page).toHaveURL(new RegExp(`a=${playerA}.*b=${playerB}|b=${playerB}.*a=${playerA}`));
  await context.close();
});
