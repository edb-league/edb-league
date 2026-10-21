// Verifica os pares de cores de src/app/tokens.css contra a WCAG 2.2.
// Uso: node scripts/check-contrast.mjs   (sai com código 1 se algum par falhar)
import { readFileSync } from "node:fs";

const css = readFileSync(new URL("../src/app/tokens.css", import.meta.url), "utf8");
const tokens = { light: {}, dark: {} };
for (const m of css.matchAll(/--([\w-]+):\s*light-dark\(\s*(#[0-9a-f]{6})\s*,\s*(#[0-9a-f]{6})\s*\)/gi)) {
  tokens.light[m[1]] = m[2];
  tokens.dark[m[1]] = m[3];
}

const lum = (hex) => {
  const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)
    .map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
};
const ratio = (a, b) => {
  const [hi, lo] = [lum(a), lum(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
};

const surfaces = ["bg", "surface", "surface-2"];
const pairs = [];
// [primeiro plano, fundos, mínimo, descrição]
const add = (fg, bgs, min, why) => bgs.forEach((bg) => pairs.push([fg, bg, min, why]));
add("text", [...surfaces, "surface-3"], 7, "texto principal (AAA)");
add("text-muted", surfaces, 7, "texto secundário (AAA)");
add("text-muted", ["surface-3"], 4.5, "texto secundário");
add("text-subtle", surfaces, 4.5, "texto terciário (AA)");
add("accent", surfaces, 4.5, "links e destaques");
add("gold", ["surface", "surface-2", "bg"], 4.5, "dourado do ranking");
add("win", surfaces, 4.5, "vitória");
add("loss", surfaces, 4.5, "derrota");
add("pt", surfaces, 4.5, "time PT");
add("pl", surfaces, 4.5, "time PL");
add("focus", surfaces, 3, "anel de foco (componente)");
add("border", surfaces, 3, "borda de controles (componente)");
pairs.push(["on-accent", "accent-bg", 7, "texto sobre botão primário"]);
pairs.push(["on-gold", "gold-bg", 7, "texto sobre botão dourado"]);
for (const n of [1, 2, 3, 4]) pairs.push([`lv${n}-fg`, `lv${n}-bg`, 4.5, `número no selo de nível (faixa ${n})`]);
pairs.push(["win", "win-bg", 4.5, "texto de vitória sobre a etiqueta"]);
pairs.push(["loss", "loss-bg", 4.5, "texto de derrota sobre a etiqueta"]);
add("gold-bg", surfaces, 3, "selo dourado (componente)");
for (const n of [1, 2, 3, 4]) add(`lv${n}-bg`, ["surface"], 3, `selo de nível ${n} sobre o cartão (componente)`);

let failed = 0;
for (const theme of ["dark", "light"]) {
  for (const [fg, bg, min, why] of pairs) {
    const a = tokens[theme][fg], b = tokens[theme][bg];
    if (!a || !b) { console.error(`token ausente: ${fg} ou ${bg}`); failed++; continue; }
    const r = ratio(a, b);
    if (r < min) { failed++; console.error(`FALHA [${theme}] ${fg} ${a} em ${bg} ${b}: ${r.toFixed(2)} < ${min} (${why})`); }
  }
}
if (failed) { console.error(`\n${failed} par(es) abaixo do mínimo.`); process.exit(1); }
console.log(`Contraste OK: ${pairs.length * 2} verificações (claro e escuro).`);
