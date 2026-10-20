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
    for (const route of ["/", "/rankings/elite", "/rankings/xp", "/partidas", "/jogadores", `/jogadores/${playerA}`, `/partidas/mapa/${mapId}`, "/sorteador", "/regulamento", "/medalhas", "/missoes-xp", "/admin"]) {
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

test("grupos do menu abrem com clique, listam os itens e fecham com Esc", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto("/");
  const nav = page.getByRole("navigation", { name: "Principal" });
  const tools = nav.getByRole("button", { name: "Ferramentas" });
  await expect(tools).toHaveAttribute("aria-expanded", "false");
  await expect(nav.getByRole("link", { name: "Sorteador de times" })).toBeHidden();
  await tools.click();
  await expect(tools).toHaveAttribute("aria-expanded", "true");
  await expect(nav.getByRole("link", { name: "Sorteador de times" })).toBeVisible();
  await expect(nav.getByRole("link", { name: "Comparar jogadores" })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(tools).toHaveAttribute("aria-expanded", "false");
  await expect(tools).toBeFocused();
  await nav.getByRole("button", { name: "Conquistas" }).click();
  await nav.getByRole("link", { name: "Hall da Fama" }).click();
  await expect(page).toHaveURL(/\/hall-da-fama$/);
  await expect(page.getByRole("navigation", { name: "Conquistas" }).getByRole("link", { name: "Hall da Fama" })).toHaveAttribute("aria-current", "page");
});

test("no celular o menu lista Sorteador e Regulamento", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 800 });
  await page.goto("/");
  await page.getByRole("button", { name: /menu/i }).click();
  const nav = page.getByRole("navigation", { name: "Principal" });
  await expect(nav.getByRole("link", { name: "Sorteador de times" })).toBeVisible();
  await expect(nav.getByRole("link", { name: "Regulamento" })).toBeVisible();
});

test("Rankings tem a aba XP", async ({ page }) => {
  await page.goto("/rankings/elite");
  await page.getByRole("navigation", { name: "Tipo de ranking" }).getByRole("link", { name: "XP" }).click();
  await expect(page).toHaveURL(/\/rankings\/xp(\?|$)/);
  await expect(page.getByRole("heading", { level: 2 }).first()).toBeVisible();
});

test("sorteador: escolhe 10 presentes, sorteia e mostra os dois times", async ({ page }) => {
  await page.goto("/sorteador");
  const sortear = page.getByRole("button", { name: "Sortear times" });
  await expect(sortear).toBeDisabled();
  const boxes = page.getByRole("group", { name: "Jogadores presentes" }).getByRole("checkbox");
  for (let i = 0; i < 10; i++) await boxes.nth(i).check();
  await expect(page.getByText("10 de 10 selecionados")).toBeVisible();
  await expect(sortear).toBeEnabled();
  await sortear.click();
  await expect(page.getByRole("region", { name: "Time PT" })).toBeVisible();
  await expect(page.getByRole("region", { name: "Time PL" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Copiar mensagem" })).toBeVisible();
});

test("regulamento tem índice lateral e as oito seções", async ({ page }) => {
  await page.goto("/regulamento");
  const toc = page.getByRole("navigation", { name: "Neste regulamento" });
  await expect(toc.getByRole("link")).toHaveCount(8);
  for (const id of ["temporadas", "confrontos", "pontuacao", "titulos", "xp", "niveis", "medalhas", "perguntas"]) {
    await expect(page.locator(`#${id}`)).toHaveCount(1);
  }
});

test("início não traz mais sorteador nem regulamento, mas tem atalhos", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Sorteador de times", level: 2 })).toHaveCount(0);
  await expect(page.getByRole("heading", { name: /Como funcionam as temporadas/ })).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "Últimas partidas" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Regulamento", exact: true }).first()).toBeVisible();
});
