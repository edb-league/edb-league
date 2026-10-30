import { expect, test } from "@playwright/test";
import { expectNoViolations, signInWithSteam } from "./helpers";

const FALCAO = "76561198000000101";

test("visitante vê a política e é convidado a entrar para escolher", async ({ page }) => {
  await page.goto("/privacidade");
  await expect(page.getByRole("heading", { level: 1, name: "Privacidade" })).toBeVisible();
  await expect(page.getByText("Nunca é mostrado a ninguém")).toBeVisible();
  await expect(page.getByRole("link", { name: "Entrar com Steam" }).first()).toBeVisible();
  await expect(page.getByRole("checkbox")).toHaveCount(0);
  await expectNoViolations(page, "privacidade (visitante)");
});

test("jogador salva a escolha e ela continua depois de recarregar", async ({ page }) => {
  await signInWithSteam(page, FALCAO, "/privacidade");
  await expect(page).toHaveURL(/\/privacidade$/);
  const box = page.getByRole("checkbox", { name: "Esconder minhas horas de CS" });
  await expect(box).toBeVisible();
  const before = await box.isChecked();   // o servidor de teste pode ser reaproveitado entre execuções

  await box.setChecked(!before);
  await page.getByRole("button", { name: "Salvar escolhas" }).click();
  await expect(page.getByRole("status")).toContainText("Escolhas salvas");

  await page.reload();
  const again = page.getByRole("checkbox", { name: "Esconder minhas horas de CS" });
  await expect(again).toBeChecked({ checked: !before });
  await expectNoViolations(page, "privacidade (logado)");

  // Deixa como estava.
  await again.setChecked(before);
  await page.getByRole("button", { name: "Salvar escolhas" }).click();
  await expect(page.getByRole("status")).toContainText("Escolhas salvas");
});
