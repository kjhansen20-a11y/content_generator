import { createHash } from "node:crypto";
import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const index = await readFile(path.join(root, "site", "index.html"));
const redirects = await readFile(path.join(root, "site", "_redirects"));

const files = {
  "/index.html": index.toString("utf8"),
  "/_redirects": redirects.toString("utf8"),
};

const manifest = {};
for (const [p, content] of Object.entries(files)) {
  manifest[p] = createHash("sha256").update(content, "utf8").digest("hex");
}

const payload = { files, manifest };
await writeFile(path.join(root, "site-deploy-payload.json"), JSON.stringify(payload));
console.log("Wrote site-deploy-payload.json");
