import { defineConfig, devices } from "@playwright/test";

const WEB = process.env.E2E_BASE_URL ?? "http://127.0.0.1:3000";
const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD ?? "demo-senha-123";
// Contas da Steam usadas nos testes de login (ver e2e/steam.spec.ts): a primeira é um jogador da demonstração.
const SESSION_SECRET = "segredo-de-e2e-com-mais-de-16-caracteres";
const ADMIN_STEAMID = "76561198000008888";

/**
 * Os testes rodam contra a API em modo demonstração (dados sintéticos, sem banco).
 * Se os servidores já estiverem no ar, são reaproveitados.
 * Em ambientes sem o Chromium do Playwright, aponte PW_CHROMIUM_PATH para um executável existente.
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 45_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL: WEB,
    locale: "pt-BR",
    timezoneId: "America/Sao_Paulo",
    trace: "retain-on-failure",
    launchOptions: process.env.PW_CHROMIUM_PATH ? { executablePath: process.env.PW_CHROMIUM_PATH } : {},
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: "python -m uvicorn --app-dir apps/web/e2e/support api_steam_simulada:app --port 8000",
      cwd: "../..",
      url: "http://127.0.0.1:8000/api/health",
      reuseExistingServer: true,
      timeout: 60_000,
      env: {
        EDB_DEMO: "1",
        XINXAS_ADMIN_PASSWORD: ADMIN_PASSWORD,
        EDB_ALLOWED_ORIGINS: WEB,
        EDB_PUBLIC_URL: WEB,
        EDB_SESSION_SECRET: SESSION_SECRET,
        EDB_ADMIN_STEAMID: ADMIN_STEAMID,
      },
    },
    {
      // Limpa o cache de dados do Next antes do build: respostas guardadas de execuções anteriores (por exemplo, /api/me
      // anônimo, que fica 5 min em cache) não podem contaminar os testes.
      command: "node -e \"require('fs').rmSync('.next/cache/fetch-cache',{recursive:true,force:true})\" && npm run build && npm run start",
      url: WEB,
      reuseExistingServer: true,
      timeout: 240_000,
      env: { API_URL: "http://127.0.0.1:8000" },
    },
  ],
});
