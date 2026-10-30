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

test("regulamento tem índice lateral e as seis seções", async ({ page }) => {
  await page.goto("/regulamento");
  const toc = page.getByRole("navigation", { name: "Neste regulamento" });
  await expect(toc.getByRole("link")).toHaveCount(6);
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

test("perfil do jogador tem abas e cada uma mostra só o seu conteúdo", async ({ page, request }) => {
  const { playerA } = await ids(request);
  await page.goto(`/jogadores/${playerA}`);
  const nav = page.getByRole("navigation", { name: "Seções do perfil" });
  await expect(nav.getByRole("link", { name: "Resumo" })).toHaveAttribute("aria-current", "page");
  await expect(page.getByRole("heading", { name: /Evolução por partida/ })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Histórico de partidas" })).toHaveCount(0);
  await nav.getByRole("link", { name: "Estatísticas" }).click();
  await expect(page.getByRole("heading", { name: /Detailed stats/ })).toBeVisible();
  await expect(page.getByRole("heading", { name: /Firepower/ })).toBeVisible();
  await nav.getByRole("link", { name: "Partidas" }).click();
  await expect(page.getByRole("heading", { name: "Histórico de partidas" })).toBeVisible();
  await nav.getByRole("link", { name: "Medalhas e títulos" }).click();
  await expect(page.getByRole("heading", { name: "Títulos de temporada" })).toBeVisible();
});

test("estatísticas: nomes em inglês com significado, sub-abas e filtros na URL", async ({ page, request }) => {
  const { playerA } = await ids(request);
  await page.goto(`/jogadores/${playerA}?aba=estatisticas`);
  // Nome da HLTV em inglês e significado em português na mesma célula.
  const kpr = page.getByRole("rowheader", { name: /Kills per round\s+kills por round/ }).first();
  await expect(kpr).toBeVisible();
  // Rating 2.0 em destaque no cabeçalho, sem idade nem país.
  await expect(page.locator("header.card").getByText("Rating 2.0")).toBeVisible();
  await expect(page.getByText(/^Idade$|^País$/)).toHaveCount(0);

  const tipos = page.getByRole("navigation", { name: "Tipos de estatística" });
  await expect(tipos.getByRole("link", { name: /Overview/ })).toHaveAttribute("aria-current", "page");
  await tipos.getByRole("link", { name: /Weapons/ }).click();
  await expect(page).toHaveURL(/vista=weapons/);
  await expect(page.getByRole("heading", { name: /Weapons/ })).toBeVisible();

  const filtros = page.getByRole("region", { name: "Filtros" });
  await filtros.getByRole("link", { name: /^CT/ }).click();
  await expect(page).toHaveURL(/lado=ct/);
  await expect(page).toHaveURL(/vista=weapons/);
  await expect(filtros.getByRole("link", { name: /^CT/ })).toHaveAttribute("aria-current", "true");
  await expect(page.getByText(/não separa armas por lado/)).toBeVisible();

  await filtros.getByRole("link", { name: "Limpar filtros" }).click();
  await expect(page).not.toHaveURL(/lado=/);
});

test("estatísticas: filtro sem partidas mostra aviso e permite limpar", async ({ page, request }) => {
  const { playerA } = await ids(request);
  await page.goto(`/jogadores/${playerA}?aba=estatisticas&mapa=Mapa-que-nao-existe`);
  await expect(page.getByText(/combina com estes filtros/)).toBeVisible();
  await page.getByRole("link", { name: "Limpar filtros" }).click();
  await expect(page.getByRole("heading", { name: /Firepower/ })).toBeVisible();
});

test("medalhas filtra por faixa", async ({ page }) => {
  await page.goto("/medalhas");
  const filtro = page.getByRole("navigation", { name: "Filtrar por faixa" });
  await filtro.getByRole("link", { name: /^Ouro/ }).click();
  await expect(page).toHaveURL(/faixa=gold/);
  await expect(page.getByRole("link", { name: /^Ouro/ })).toHaveAttribute("aria-current", "page");
  await expect(page.getByText("Bronze", { exact: true })).toHaveCount(0);
});

test("política de conteúdo ativa e nenhuma página viola a própria política", async ({ page, request }) => {
  const { playerA, mapId } = await ids(request);
  const violations: string[] = [];
  page.on("console", (message) => {
    if (/content security policy/i.test(message.text())) violations.push(message.text());
  });
  const home = await page.goto("/");
  const csp = home?.headers()["content-security-policy"] ?? "";
  expect(csp).toContain("frame-ancestors 'none'");
  expect(csp).toContain("object-src 'none'");
  expect(csp).not.toContain("*;");
  for (const route of ["/", "/rankings/elite", "/jogadores", `/jogadores/${playerA}`, `/partidas/mapa/${mapId}`, "/sorteador", "/comparar", "/medalhas", "/hall-da-fama", "/temporadas", "/admin"]) {
    await page.goto(route);
    await page.waitForLoadState("networkidle");
  }
  expect(violations, violations.join("\n")).toEqual([]);
});

test("temporadas: arquivo lista cada ciclo com números, títulos e atalhos", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto("/");
  const nav = page.getByRole("navigation", { name: "Principal" });
  await nav.getByRole("button", { name: "Conquistas" }).click();
  await nav.getByRole("link", { name: "Temporadas" }).click();
  await expect(page).toHaveURL(/\/temporadas$/);
  await expect(page.getByRole("heading", { level: 1, name: "Temporadas" })).toBeVisible();
  const first = page.getByRole("region").filter({ has: page.getByRole("link", { name: "Ver rankings" }) }).first();
  await expect(first.getByText("Mapas", { exact: true })).toBeVisible();
  await expect(first.getByRole("list", { name: /Campeões oficiais|Líderes até agora/ })).toBeVisible();
  await first.getByRole("link", { name: "Ver rankings" }).click();
  await expect(page).toHaveURL(/\/rankings\/elite\?temporada=\d+/);
});
