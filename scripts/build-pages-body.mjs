import { createHash } from "node:crypto";
import { readdir, readFile, stat, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const siteDir = path.resolve(__dirname, "..", "site");
const outFile = path.resolve(__dirname, "..", "site-deploy-body.bin");

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
const manifest = {};
const fileParts = [];
for (const { rel, full } of fileEntries) {
  const buf = await readFile(full);
  const h = createHash("sha256").update(buf).digest("hex");
  manifest[`/${rel.replace(/\\/g, "/")}`] = h;
  fileParts.push({ hash: h, buf });
}

const boundary = "----pagesdeploy" + Date.now();
const chunks = [];
chunks.push(Buffer.from(`--${boundary}\r\nContent-Disposition: form-data; name="manifest"\r\nContent-Type: application/json\r\n\r\n${JSON.stringify(manifest)}\r\n`));
for (const { hash, buf } of fileParts) {
  chunks.push(Buffer.from(`--${boundary}\r\nContent-Disposition: form-data; name="${hash}"; filename="file"\r\nContent-Type: application/octet-stream\r\n\r\n`));
  chunks.push(buf);
  chunks.push(Buffer.from("\r\n"));
}
chunks.push(Buffer.from(`--${boundary}--\r\n`));
const body = Buffer.concat(chunks);
await writeFile(outFile, body);
console.log(JSON.stringify({ boundary, bytes: body.length, manifest, outFile }));
