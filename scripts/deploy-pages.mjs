#!/usr/bin/env node
/**
 * Deploy site/ to Cloudflare Pages via Direct Upload API.
 * Requires CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID env vars.
 *
 * Usage: node scripts/deploy-pages.mjs [project-name]
 */
import { createHash } from "node:crypto";
import { readdir, readFile, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const siteDir = path.resolve(__dirname, "..", "site");
const project = process.argv[2] || "kredesolutions";
const accountId = process.env.CLOUDFLARE_ACCOUNT_ID || "c1743ecfdf4677e26468493cc45f9cbe";
const token = process.env.CLOUDFLARE_API_TOKEN;

if (!token) {
  console.error("Set CLOUDFLARE_API_TOKEN to deploy.");
  process.exit(1);
}

async function walk(dir, base = "") {
  const entries = await readdir(dir);
  const files = [];
  for (const name of entries) {
    const full = path.join(dir, name);
    const rel = base ? `${base}/${name}` : name;
    const st = await stat(full);
    if (st.isDirectory()) {
      files.push(...(await walk(full, rel)));
    } else {
      files.push({ rel, full });
    }
  }
  return files;
}

function hashBuffer(buf) {
  return createHash("sha256").update(buf).digest("hex");
}

const fileEntries = await walk(siteDir);
const manifest = {};
const fileParts = [];

for (const { rel, full } of fileEntries) {
  const buf = await readFile(full);
  const h = hashBuffer(buf);
  const key = `/${rel.replace(/\\/g, "/")}`;
  manifest[key] = h;
  fileParts.push({ hash: h, buf });
}

const boundary = "----pagesdeploy" + Date.now();
const chunks = [];

chunks.push(`--${boundary}\r\n`);
chunks.push('Content-Disposition: form-data; name="manifest"\r\n');
chunks.push("Content-Type: application/json\r\n\r\n");
chunks.push(JSON.stringify(manifest) + "\r\n");

for (const { hash, buf } of fileParts) {
  chunks.push(`--${boundary}\r\n`);
  chunks.push(`Content-Disposition: form-data; name="${hash}"; filename="file"\r\n`);
  chunks.push("Content-Type: application/octet-stream\r\n\r\n");
  chunks.push(buf);
  chunks.push("\r\n");
}
chunks.push(`--${boundary}--\r\n`);

const body = Buffer.concat(chunks.map((c) => (Buffer.isBuffer(c) ? c : Buffer.from(c, "utf8"))));

const res = await fetch(
  `https://api.cloudflare.com/client/v4/accounts/${accountId}/pages/projects/${project}/deployments`,
  {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": `multipart/form-data; boundary=${boundary}`,
    },
    body,
  }
);

const json = await res.json();
if (!json.success) {
  console.error("Deploy failed:", JSON.stringify(json, null, 2));
  process.exit(1);
}
console.log("Deployed:", json.result.url);
