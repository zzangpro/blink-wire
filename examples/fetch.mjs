#!/usr/bin/env node
// Pull new articles from BLINK Wire. Node 18+, no dependencies.
//
//   export BLINK_WIRE_KEY=...
//   node fetch.mjs --since 2026-09-01T00:00:00 --out ./articles
//
// Listing is free, so this lists first and fetches only what it has not taken before.
// `already_taken` is per key and comes from the server, so this stays correct even if you
// lose local state — you will not be billed twice for the same article.

import { mkdir, writeFile } from "node:fs/promises";
import { argv, env, exit } from "node:process";

const BASE = env.BLINK_WIRE_BASE ?? "https://wire.blinkhub.net";
const KEY = env.BLINK_WIRE_KEY ?? "";

function arg(name, fallback) {
  const i = argv.indexOf(`--${name}`);
  return i === -1 ? fallback : argv[i + 1];
}
const dryRun = argv.includes("--dry-run");

async function call(path, params = {}) {
  const url = new URL(path, BASE);
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null) url.searchParams.set(k, v);
  }
  const res = await fetch(url, { headers: { "X-Api-Key": KEY } });
  if (!res.ok) {
    let code = String(res.status);
    try {
      code = (await res.json())?.error?.code ?? code;
    } catch {
      /* body was not JSON */
    }
    console.error(`HTTP ${res.status} (${code}) on ${path}`);
    exit(1);
  }
  return { body: await res.json(), headers: res.headers };
}

if (!KEY) {
  console.error("set BLINK_WIRE_KEY");
  exit(1);
}

const market = arg("market", "us");
const { body: listing } = await call("/api/wire/v1/articles", {
  market,
  limit: arg("limit", "20"),
  since: arg("since"),
});

const fresh = listing.items.filter((i) => !i.already_taken);
console.error(`${listing.count} available, ${fresh.length} not yet taken`);

if (dryRun) {
  for (const i of listing.items) {
    const mark = i.already_taken ? " " : "*";
    console.log(`${mark} ${String(i.id).padStart(8)}  ${(i.source ?? "-").padEnd(28)} ${i.headline.slice(0, 70)}`);
  }
  exit(0);
}

const out = arg("out", "./articles");
await mkdir(out, { recursive: true });

let spent = 0;
for (const i of fresh) {
  const { body: doc, headers } = await call(`/api/wire/v1/articles/${i.id}`, { market });
  await writeFile(`${out}/${i.id}.json`, JSON.stringify(doc, null, 2), "utf8");
  const charged = Number(headers.get("x-wire-credits-charged") ?? 0);
  spent += charged;
  console.error(`saved ${i.id} (charged ${charged}, balance ${headers.get("x-wire-credits-balance") ?? "?"})`);
}

console.error(`done — ${fresh.length} articles, ${spent} charged`);
