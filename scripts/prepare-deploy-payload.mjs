import { createHash } from "node:crypto";
import { readdir, readFile, stat, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const siteDir = path.join(root, "site");

async function walk(dir, base = "") {
  const entries = await readdir(dir);
  const files = [];
  for (const name of entries) {
    const full = path.join(dir, name);
    const rel = base ? `${base}/${name}` : name;
    const st = await stat(full);
    if (st.isDirectory()) files.push(...(await walk(full, rel)));
    else files.push({ rel, full });
  }
  return files;
}

const fileEntries = await walk(siteDir);
const files = {};
const manifest = {};

for (const { rel, full } of fileEntries) {
  const content = await readFile(full);
  const key = `/${rel.replace(/\\/g, "/")}`;
  files[key] = content.toString("utf8");
  manifest[key] = createHash("sha256").update(content).digest("hex");
}

const payload = { files, manifest };
await writeFile(path.join(root, "site-deploy-payload.json"), JSON.stringify(payload));
console.log("Wrote site-deploy-payload.json", Object.keys(files).sort());
