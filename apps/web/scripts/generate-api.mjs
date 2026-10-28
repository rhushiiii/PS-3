import { spawnSync } from "node:child_process";
import { readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import prettier from "prettier";

const web = fileURLToPath(new URL("../", import.meta.url));
const python = resolve(
  web,
  "../../services/api/.venv",
  process.platform === "win32" ? "Scripts/python.exe" : "bin/python",
);
const schema = spawnSync(python, [resolve(web, "scripts/export-openapi.py")], {
  cwd: web,
  encoding: "utf8",
  maxBuffer: 8 * 1024 * 1024,
});
if (schema.status !== 0)
  throw new Error(
    "OpenAPI export failed. Install the API's locked requirements first.",
  );
const generated = spawnSync(
  process.execPath,
  [resolve(web, "tools/api-types/generate.mjs")],
  {
    input: schema.stdout,
    cwd: web,
    encoding: "utf8",
    maxBuffer: 8 * 1024 * 1024,
  },
);
if (generated.status !== 0)
  throw new Error(
    "Type generation failed. Run npm ci --prefix tools/api-types first.",
  );
const output = await prettier.format(
  "// Generated from FastAPI OpenAPI. Run npm run api:generate; do not edit.\n" +
    generated.stdout,
  {
    ...(await prettier.resolveConfig(web)),
    parser: "typescript",
  },
);
const target = resolve(web, "src/lib/api/generated.d.ts");
if (process.argv.includes("--check")) {
  if ((await readFile(target, "utf8")) !== output)
    throw new Error(
      "API types differ from the backend. Run npm run api:generate.",
    );
  process.stdout.write("Generated API types match the backend.\n");
} else {
  await writeFile(target, output);
  process.stdout.write("Generated src/lib/api/generated.d.ts\n");
}
