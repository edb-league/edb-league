import { expect, test } from "@playwright/test";
import { ids } from "./helpers";

/** Pré-visualização de links (WhatsApp, Discord, X): metadados Open Graph e imagem 1200×630 de cada tipo de página. */
async function expectImage(request: import("@playwright/test").APIRequestContext, url: string) {
  const response = await request.get(url);
  expect(response.status(), url).toBe(200);
  expect(response.headers()["content-type"], url).toContain("image/png");
  const body = await response.body();
  expect(body.subarray(1, 4).toString(), url).toBe("PNG");
  // IHDR: largura e altura em big-endian logo após a assinatura.
  expect([body.readUInt32BE(16), body.readUInt32BE(20)], url).toEqual([1200, 630]);
}

test("páginas compartilháveis declaram imagem e cartão grande", async ({ page, request }) => {
  const { playerA, mapId } = await ids(request);
  for (const path of ["/", "/rankings/elite", `/jogadores/${playerA}`, `/partidas/mapa/${mapId}`]) {
    await page.goto(path);
    const image = await page.locator('meta[property="og:image"]').getAttribute("content");
    expect(image, path).toContain("opengraph-image");
    await expect(page.locator('meta[property="og:image:width"]')).toHaveAttribute("content", "1200");
    await expect(page.locator('meta[name="twitter:card"]')).toHaveAttribute("content", "summary_large_image");
    await expect(page.locator('meta[property="og:description"]')).not.toHaveAttribute("content", "");
  }
});

test("as imagens de pré-visualização são PNG 1200×630", async ({ request }) => {
  const { playerA, mapId } = await ids(request);
  for (const url of [
    "/opengraph-image",
    "/rankings/elite/opengraph-image",
    "/rankings/xp/opengraph-image",
    `/jogadores/${playerA}/opengraph-image`,
    `/partidas/mapa/${mapId}/opengraph-image`,
  ]) {
    await expectImage(request, url);
  }
});

test("imagem de jogador inexistente cai na imagem genérica em vez de quebrar", async ({ request }) => {
  await expectImage(request, "/jogadores/nao-existe/opengraph-image");
});
