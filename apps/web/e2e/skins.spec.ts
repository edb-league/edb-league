import { expect, test } from "@playwright/test";
import { expectNoViolations } from "./helpers";

test.describe("Skins: inventário por arma", () => {
  test("lado TR/CT mostra só as armas de cada lado e a escolha vira prévia", async ({ page }) => {
    await page.goto("/skins");
    const tr = page.getByRole("button", { name: "TR", exact: true });
    const ct = page.getByRole("button", { name: "CT", exact: true });
    await expect(tr).toHaveAttribute("aria-pressed", "true");

    // TR: AK-47 existe, M4A1-S não.
    await expect(page.getByRole("button", { name: /AK-47/ })).toBeVisible();
    await expect(page.getByRole("button", { name: /M4A1-S/ })).toHaveCount(0);

    // CT: o contrário.
    await ct.click();
    await expect(ct).toHaveAttribute("aria-pressed", "true");
    await expect(page.getByRole("button", { name: /M4A1-S/ })).toBeVisible();
    await expect(page.getByRole("button", { name: /AK-47/ })).toHaveCount(0);

    // Armas dos dois lados aparecem nos dois (AWP).
    await expect(page.getByRole("button", { name: /AWP/ })).toBeVisible();
    await tr.click();
    await expect(page.getByRole("button", { name: /AWP/ })).toBeVisible();

    // Abre a AK-47, marca uma skin e volta: a casa mostra a skin escolhida.
    await page.getByRole("button", { name: /AK-47/ }).click();
    await expect(page.getByRole("heading", { level: 3, name: /AK-47/ })).toBeFocused();
    const skin = page.getByRole("button", { name: "Bloodsport" });
    await skin.click();
    await expect(skin).toHaveAttribute("aria-pressed", "true");
    await expect(page.getByText("Em uso")).toBeVisible();
    await expectNoViolations(page, "/skins com arma aberta e skin em uso");
    await page.getByRole("button", { name: "← Armas" }).click();
    await expect(page.getByRole("button", { name: /AK-47/ })).toBeFocused();
    await expect(page.getByRole("button", { name: /AK-47.*Bloodsport/ })).toBeVisible();

    // A escolha é do lado TR: no CT a AK-47 nem aparece, e no TR continua depois de recarregar.
    await page.reload();
    await expect(page.getByRole("button", { name: /AK-47.*Bloodsport/ })).toBeVisible();
  });

  test("cada lado usa uma faca só: o slot Faca lista os modelos e escolher outra skin troca a anterior", async ({ page }) => {
    // Vale para o catálogo de exemplo e para o real: Karambit e M9 Bayonet existem nos dois.
    await page.goto("/skins");
    const slot = page.locator('[data-weapon="slot|knife"]');
    await expect(slot).toContainText("Faca padrão");
    // Os modelos não aparecem soltos na lista de armas.
    await expect(page.getByRole("button", { name: /^Karambit/ })).toHaveCount(0);

    await slot.click();
    await expect(page.getByRole("heading", { level: 3, name: /Faca/ })).toBeFocused();
    await page.getByRole("button", { name: /Karambit/ }).click();
    await expect(page.getByRole("heading", { level: 3, name: /Karambit/ })).toBeFocused();
    await page.locator("ul button[aria-pressed]").first().click();
    await expect(page.getByText("Em uso")).toHaveCount(1);
    await expectNoViolations(page, "/skins com modelo de faca aberto e skin em uso");

    // Volta para os modelos: o Karambit marca "Em uso" e recebe o foco.
    await page.getByRole("button", { name: "← Modelos" }).click();
    await expect(page.getByRole("button", { name: /Karambit/ })).toBeFocused();
    await expect(page.getByText("Em uso")).toHaveCount(1);
    await expectNoViolations(page, "/skins com a lista de modelos de faca");

    // Escolher uma skin de outro modelo troca a faca: só o novo modelo fica em uso.
    await page.getByRole("button", { name: /M9 Bayonet/ }).click();
    await page.locator("ul button[aria-pressed]").first().click();
    await page.getByRole("button", { name: "← Modelos" }).click();
    await expect(page.getByText("Em uso")).toHaveCount(1);
    await expect(page.getByRole("button", { name: /M9 Bayonet.*Em uso|Em uso.*M9 Bayonet/ })).toBeVisible();

    // No TR a faca aparece com o modelo; no CT o slot é outro e segue no padrão.
    await page.getByRole("button", { name: "← Armas" }).click();
    await expect(slot).toContainText("M9 Bayonet");
    await page.getByRole("button", { name: "CT", exact: true }).click();
    await expect(slot).toContainText("Faca padrão");
  });

  test("a busca acha a arma pelo nome da arma e da skin, e avisa quando não há resultado", async ({ page }) => {
    // O catálogo pode ser o de exemplo ou o real (no CI), então só se afirma o que vale nos dois:
    // a AWP existe e tem uma Asiimov; uma busca sem sentido não acha nada.
    await page.goto("/skins");
    const busca = page.getByRole("searchbox", { name: "Pesquisar arma ou skin" });
    await busca.fill("awp");
    await expect(page.getByRole("button", { name: /AWP/ })).toBeVisible();
    await expect(page.getByRole("button", { name: /Glock-18/ })).toHaveCount(0);
    await busca.fill("asiimov");
    await expect(page.getByRole("button", { name: /AWP/ })).toBeVisible();
    await busca.fill("zzzz-sem-resultado");
    await expect(page.getByText("Nenhum item encontrado.")).toBeVisible();
  });
});
