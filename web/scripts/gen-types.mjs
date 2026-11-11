// Gera os tipos TypeScript a partir dos JSON Schemas do contrato (que saem dos modelos Pydantic).
// Se o motor mudar o formato, `npm run typecheck` quebra aqui antes de o painel quebrar em produção.
import { readFileSync, readdirSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { compile } from "json-schema-to-typescript";

const here = dirname(fileURLToPath(import.meta.url));
const schemas = resolve(here, "..", "..", "schemas");
const out = resolve(here, "..", "src", "contract");
mkdirSync(out, { recursive: true });

for (const file of readdirSync(schemas).filter((f) => f.endsWith(".schema.json"))) {
  const schema = JSON.parse(readFileSync(join(schemas, file), "utf-8"));
  const ts = await compile(schema, schema.title, {
    bannerComment: `/* Gerado por scripts/gen-types.mjs a partir de schemas/${file}. Não edite à mão. */`,
    additionalProperties: false,
    style: { singleQuote: false },
  });
  const name = file.replace(".schema.json", ".ts");
  // O Pydantic descreve tuplas com prefixItems (JSON Schema 2020-12), que o json2ts não lê:
  // os ICs são sempre pares de números.
  writeFileSync(join(out, name), ts.replaceAll("[unknown, unknown]", "[number, number]"));
  console.log(`tipos gerados: src/contract/${name}`);
}
