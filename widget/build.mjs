import { copyFile, mkdir, rm } from "node:fs/promises";
import { join } from "node:path";
import { build } from "esbuild";

await rm("dist", { recursive: true, force: true });
await mkdir("dist/i18n", { recursive: true });
await mkdir("dist/images", { recursive: true });
await build({
  entryPoints: ["src/script.ts"],
  bundle: true,
  outfile: "dist/script.js",
  format: "iife",
  target: "es2020",
  minify: true
});
await copyFile("src/styles.css", "dist/styles.css");
await copyFile("public/i18n/ru.json", "dist/i18n/ru.json");
await copyFile("public/i18n/en.json", "dist/i18n/en.json");
for (const mode of ["private", "public"]) {
  await copyFile(`public/manifest.${mode}.json`, join("dist", `manifest.${mode}.json`));
}
