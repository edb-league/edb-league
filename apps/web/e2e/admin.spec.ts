import path from "node:path";
import { expect, test } from "@playwright/test";
import { expectNoViolations, loginAsAdmin } from "./helpers";

test("senha errada mostra erro sem entrar", async ({ page }) => {
  await page.goto("/admin");
  await page.getByLabel("Senha do administrador").fill("senha-errada");
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page.getByRole("alert").filter({ hasText: "Senha incorreta" })).toBeVisible();
  await expect(page.getByRole("tab", { name: "Elenco" })).toHaveCount(0);
});

test("rotas de administração exigem sessão", async ({ request }) => {
  expect((await request.get("/api/admin/overview")).status()).toBe(401);
  expect((await request.get("/api/admin/export/players.csv")).status()).toBe(401);
});

test("fluxo completo: elenco, importar amostra e sair", async ({ page }) => {
  await loginAsAdmin(page);

  const nick = `Teste${Date.now() % 100000}`;
  await page.getByLabel("Nickname", { exact: true }).first().fill(nick);
  await page.getByRole("button", { name: "Adicionar jogador" }).click();
  await expect(page.getByText("Jogador cadastrado.")).toBeVisible();

  await page.getByRole("tab", { name: "Importar", exact: true }).click();
  await page.getByRole("radio", { name: /Exemplo da liga/ }).check();
  await page.getByRole("button", { name: "Ler partida" }).click();
  await expect(page.getByRole("heading", { name: "Conferir e gravar" })).toBeVisible();
  await expect(page.getByRole("table")).toBeVisible();

  await page.getByRole("tab", { name: "Exportar" }).click();
  const csv = await page.request.get("/api/admin/export/players.csv");
  expect(csv.status()).toBe(200);
  expect(await csv.text()).toContain(nick);

  await page.getByRole("button", { name: "Sair da administração" }).click();
  await expect(page.getByLabel("Senha do administrador")).toBeVisible();
});

test("campos do formulário têm rótulo e navegação por teclado nas abas", async ({ page }) => {
  await loginAsAdmin(page);
  const first = page.getByRole("tab", { name: "Elenco" });
  await first.focus();
  await page.keyboard.press("ArrowRight");
  await expect(page.getByRole("tab", { name: "Importar", exact: true })).toBeFocused();
  await page.keyboard.press("End");
  await expect(page.getByRole("tab", { name: "Exportar" })).toBeFocused();
});

test("importar série: prévia por mapa, contas pendentes e acessibilidade", async ({ page }) => {
  const fixtures = path.join(__dirname, "fixtures");
  await loginAsAdmin(page);
  await page.getByRole("tab", { name: "Importar série" }).click();
  await page
    .getByLabel("Arquivos da série")
    .setInputFiles([path.join(fixtures, "md3_inferno_25_10_1.edb.json"), path.join(fixtures, "md3_mirage_25_10_2.edb.json")]);
  await page.getByRole("button", { name: "Ler série" }).click();

  await expect(page.getByRole("heading", { name: /Mapa 1 · Inferno/ })).toBeVisible();
  await expect(page.getByRole("heading", { name: /Mapa 2 · Mirage/ })).toBeVisible();
  await expect(page.getByText("Temporada 1", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Gravar série" })).toBeDisabled();

  await page.getByRole("button", { name: "Criar como novos os que faltam" }).click();
  await expect(page.getByRole("button", { name: "Gravar série" })).toBeEnabled();
  await expectNoViolations(page, "/admin importar série");
});
