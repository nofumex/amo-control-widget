import { createWriteStream } from "node:fs";
import { mkdir, copyFile } from "node:fs/promises";
import archiver from "archiver";

const mode = process.argv[2] || "private";
if (!["private", "public"].includes(mode)) {
  throw new Error("Mode must be private or public");
}
await mkdir("dist", { recursive: true });
await copyFile(`dist/manifest.${mode}.json`, "dist/manifest.json");

const output = createWriteStream(`widget-${mode}.zip`);
const archive = archiver("zip", { zlib: { level: 9 } });
archive.pipe(output);
archive.file("dist/manifest.json", { name: "manifest.json" });
archive.file("dist/script.js", { name: "script.js" });
archive.file("dist/styles.css", { name: "styles/styles.css" });
archive.directory("dist/i18n", "i18n");
archive.directory("dist/images", "images");
await archive.finalize();
