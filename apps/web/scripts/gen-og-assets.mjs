// Gera src/lib/og/assets.ts: fontes e brasão embutidos em base64 para as imagens de pré-visualização (next/og).
// Embutir evita depender de rastreio de arquivos na Vercel. Rode de apps/web: node scripts/gen-og-assets.mjs
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import sharp from "sharp";

const font = (pkg, file) => readFileSync(`node_modules/@fontsource/${pkg}/files/${file}`).toString("base64");
const crest = (await sharp("public/crest.webp").resize({ height: 160 }).png().toBuffer()).toString("base64");

mkdirSync("src/lib/og", { recursive: true });
writeFileSync(
  "src/lib/og/assets.ts",
  `// Arquivo gerado por scripts/gen-og-assets.mjs. Não edite à mão.
export const TITLE_FONT = "${font("barlow-condensed", "barlow-condensed-latin-700-normal.woff")}";
export const BODY_FONT = "${font("barlow", "barlow-latin-600-normal.woff")}";
export const CREST_PNG = "data:image/png;base64,${crest}";
`,
);
console.log("src/lib/og/assets.ts gerado");
