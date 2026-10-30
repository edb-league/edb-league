import { expect, test } from "@playwright/test";
import { expectNoViolations, signInWithSteam } from "./helpers";

/** Falcão (SteamID da demonstração) joga as partidas da demonstração; a API de teste mantém a votação aberta. */
const FALCAO = "76561198000000101";

async function falcaoMatch(request: import("@playwright/test").APIRequestContext) {
  const players = (await (await request.get("/api/players")).json()) as { id: string; nickname: string }[] | { players: { id: string; nickname: string }[] };
  const list = Array.isArray(players) ? players : players.players;
  const falcao = list.find((p) => p.nickname === "Falcão")!;
  const detail = (await (await request.get(`/api/players/${falcao.id}`)).json()) as { matches: { match_id: string }[] };
  return detail.matches[0].match_id;
}

test("quem não entrou vê a votação aberta, sem resultado, e o convite para entrar com a Steam", async ({ page, request }) => {
  const matchId = await falcaoMatch(request);
  await page.goto(`/partidas/mapa/${matchId}`);
  const card = page.getByRole("region", { name: "MVP da partida" });
  await expect(card).toBeVisible();
  await expect(card.getByText("Votação aberta")).toBeVisible();
  await expect(card.getByRole("link", { name: "Entrar com Steam" })).toBeVisible();
  await expect(card.getByRole("list", { name: "Resultado da votação de MVP" })).toHaveCount(0);
});

test("jogador do mapa vota, troca o voto e não pode votar em si mesmo", async ({ page, request }) => {
  const matchId = await falcaoMatch(request);
  await signInWithSteam(page, FALCAO, `/partidas/mapa/${matchId}`);
  await expect(page).toHaveURL(new RegExp(`/partidas/mapa/${matchId}$`));
  const card = page.getByRole("region", { name: "MVP da partida" });
  const select = card.getByLabel("Seu voto");
  await expect(select).toBeVisible();
  await expect(select.locator("option", { hasText: "Falcão" })).toHaveCount(0);

  // Escolhe sempre uma opção diferente da atual (o servidor de teste pode ser reaproveitado entre execuções).
  const values = await select.locator("option").evaluateAll((o) => (o as HTMLOptionElement[]).map((x) => x.value).filter(Boolean));
  const current = await select.inputValue();
  const [first, second] = values.filter((v) => v !== current);
  const submit = card.getByRole("button", { name: /^(Votar|Trocar voto)$/ });

  await select.selectOption(first);
  await submit.click();
  await expect(card.getByRole("status")).toContainText("Voto registrado");
  await expect(card.getByText(/\d+ votos? de/)).toBeVisible();
  const cast = await card.getByText(/\d+ votos? de/).innerText();

  await select.selectOption(second);
  await expect(card.getByRole("button", { name: "Trocar voto" })).toBeEnabled();
  await submit.click();
  await expect(card.getByRole("status")).toContainText("Voto registrado");
  expect(await card.getByText(/\d+ votos? de/).innerText()).toBe(cast);   // foi troca, não voto novo
  await expect(card.getByRole("list", { name: "Resultado da votação de MVP" })).toHaveCount(0);
  await expectNoViolations(page, "votação de MVP aberta");
});
