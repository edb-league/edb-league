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

function nonce(): string {
  const stamp = new Date().toISOString().replace(/\.\d+Z$/, "Z");
  return `${stamp}${Math.random().toString(36).slice(2, 10)}`;
}

/**
 * Faz de conta que a pessoa entrou na Steam com esta conta. O início do login é pedido sem seguir o redirecionamento
 * (o cookie de estado vai para o navegador, que compartilha o armazenamento com page.request); depois o navegador
 * abre o endereço de retorno com a resposta que a Steam daria.
 */
export async function signInWithSteam(page: Page, steamid: string, next: string) {
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
