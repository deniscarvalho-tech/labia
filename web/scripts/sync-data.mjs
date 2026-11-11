// Copia os arquivos do contrato de dados para public/data. O painel só lê o que estiver aqui.
import { copyFileSync, existsSync, mkdirSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const target = resolve(dirname(fileURLToPath(import.meta.url)), "..", "public", "data");
mkdirSync(target, { recursive: true });

const files = [
  ["results/summary.json", "summary.json"],
  ["results/metrics.json", "metrics.json"],
  ["results/replay.json", "replay.json"],
  ["results/audit_findings.json", "audit_findings.json"],
  ["site-data/versions.json", "versions.json"],
];
for (const [from, to] of files) {
  const source = join(root, from);
  if (!existsSync(source)) {
    console.error(`faltando ${from}: rode \`make samples\` ou a avaliação antes`);
    process.exit(1);
  }
  copyFileSync(source, join(target, to));
  console.log(`copiado ${from}`);
}
