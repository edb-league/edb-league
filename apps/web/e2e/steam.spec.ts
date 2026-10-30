import { expect, test, type Page } from "@playwright/test";
import { expectNoViolations } from "./helpers";

/**
 * Login com a Steam de ponta a ponta no navegador. A Steam não é chamada: o teste intercepta o redirecionamento
 * para steamcommunity.com e devolve ao site a resposta que a Steam daria. A API de teste (api_steam_simulada.py)
 * aceita a assinatura; estado, endereço de retorno, nonce e identidade continuam sendo verificados de verdade.
 */
const PLAYER = { steamid: "76561198000000101", nickname: "Falcão" };
const ADMIN_STEAMID = "76561198000008888";
const STRANGER = "76561198000009999";

function nonce(): string {
  const stamp = new Date().toISOString().replace(/\.\d+Z$/, "Z");
  return `${stamp}${Math.random().toString(36).slice(2, 10)}`;
}

/**
 * Faz de conta que a pessoa entrou na Steam com esta conta. O início do login é pedido sem seguir o redirecionamento
 * (o cookie de estado vai para o navegador, que compartilha o armazenamento com page.request); depois o navegador
 * abre o endereço de retorno com a resposta que a Steam daria.
 */
async function signIn(page: Page, steamid: string, next: string) {
  const start = await page.request.get(`/api/auth/steam/login?next=${encodeURIComponent(next)}`, { maxRedirects: 0 });
  expect(start.status()).toBe(303);
  const toSteam = new URL(start.headers()["location"]);
  expect(`${toSteam.origin}${toSteam.pathname}`).toBe("https://steamcommunity.com/openid/login");
  const returnTo = toSteam.searchParams.get("openid.return_to")!;
  const identity = `https://steamcommunity.com/openid/id/${steamid}`;
  const answer = new URLSearchParams({
    "openid.ns": "http://specs.openid.net/auth/2.0",
    "openid.mode": "id_res",
    "openid.op_endpoint": "https://steamcommunity.com/openid/login",
    "openid.claimed_id": identity,
    "openid.identity": identity,
    "openid.return_to": returnTo,
    "openid.response_nonce": nonce(),
    "openid.assoc_handle": "1234",
    "openid.signed": "signed,op_endpoint,claimed_id,identity,return_to,response_nonce,assoc_handle",
    "openid.sig": "assinatura-de-teste",
    state: new URL(returnTo).searchParams.get("state")!,
  });
  await page.goto(`${returnTo.split("?")[0]}?${answer}`);
}

test("jogador cadastrado entra, volta à página de origem, não vira admin e sai", async ({ page }) => {
  await signIn(page, PLAYER.steamid, "/rankings/elite");
  await expect(page).toHaveURL(/\/rankings\/elite$/);
  const menu = page.getByRole("button", { name: new RegExp(PLAYER.nickname) });
  await expect(menu.first()).toBeVisible();
  await expect(page.getByRole("link", { name: "Entrar com Steam" })).toHaveCount(0);

  await menu.first().click();
  await expect(page.getByRole("link", { name: "Meu perfil" }).first()).toBeVisible();
  // O rodapé tem um link público para /admin; o que não pode existir é o item no menu da pessoa logada.
  const userMenu = page.getByRole("list").filter({ has: page.getByRole("button", { name: "Sair", exact: true }) });
  await expect(userMenu.getByRole("link", { name: "Meu perfil" })).toBeVisible();
  await expect(userMenu.getByRole("link", { name: "Administração" })).toHaveCount(0);

  // A sessão de jogador não abre a administração.
  await page.goto("/admin");
  await expect(page.getByLabel("Senha do administrador")).toBeVisible();
  expect((await page.request.get("/api/admin/overview")).status()).toBe(401);

  await page.goto("/rankings/elite");
  await page.getByRole("button", { name: new RegExp(PLAYER.nickname) }).first().click();
  await page.getByRole("button", { name: "Sair", exact: true }).first().click();
  await expect(page.getByRole("link", { name: "Entrar com Steam" }).first()).toBeVisible();
  expect((await (await page.request.get("/api/me")).json()).authenticated).toBe(false);
});

test("a conta Steam do administrador abre a administração sem senha", async ({ page }) => {
  await signIn(page, ADMIN_STEAMID, "/admin");
  await expect(page).toHaveURL(/\/admin$/);
  await expect(page.getByRole("tab", { name: "Elenco" })).toBeVisible();
  expect((await page.request.get("/api/admin/overview")).status()).toBe(200);

  await page.getByRole("button", { name: "Sair da administração" }).click();
  await expect(page.getByLabel("Senha do administrador")).toBeVisible();
  expect((await page.request.get("/api/admin/overview")).status()).toBe(401);
});

test("conta Steam sem cadastro é recusada com aviso claro e sem sessão", async ({ page }) => {
  await signIn(page, STRANGER, "/rankings/elite");
  await expect(page).toHaveURL(/login=desconhecido/);
  await expect(page.getByText("Seu SteamID ainda não está cadastrado")).toBeVisible();
  expect((await (await page.request.get("/api/me")).json()).authenticated).toBe(false);
  await expectNoViolations(page, "aviso de login recusado");

  await page.getByRole("button", { name: "Entendi" }).click();
  await expect(page.getByText("Seu SteamID ainda não está cadastrado")).toHaveCount(0);
  await expect(page).not.toHaveURL(/login=/);
});

test("resposta sem o estado do início do login é recusada", async ({ page }) => {
  await page.goto("/api/auth/steam/callback?state=inventado");
  await expect(page).toHaveURL(/login=erro/);
  await expect(page.getByText("Não foi possível entrar com a Steam")).toBeVisible();
  expect((await (await page.request.get("/api/me")).json()).authenticated).toBe(false);
});
