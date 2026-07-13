import { createHash } from "node:crypto";
import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const buf = await readFile(path.join(root, "site", "index.html"));
const h = createHash("sha256").update(buf).digest("hex");
const manifest = { "/index.html": h };
const boundary = "----pagesdeploy" + Date.now();
const chunks = [
  Buffer.from(
    `--${boundary}\r\nContent-Disposition: form-data; name="manifest"\r\nContent-Type: application/json\r\n\r\n${JSON.stringify(manifest)}\r\n`
  ),
  Buffer.from(
    `--${boundary}\r\nContent-Disposition: form-data; name="${h}"; filename="file"\r\nContent-Type: application/octet-stream\r\n\r\n`
  ),
  buf,
  Buffer.from(`\r\n--${boundary}--\r\n`),
];
const body = Buffer.concat(chunks);
await writeFile(path.join(root, "site-deploy-index-only.b64"), body.toString("base64"));
console.log(JSON.stringify({ boundary, h, bytes: body.length }));
