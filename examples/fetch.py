#!/usr/bin/env python3
"""Pull new articles from BLINK Wire. Standard library only.

    export BLINK_WIRE_KEY=...
    python3 fetch.py --since 2026-09-01T00:00:00 --out ./articles

Listing is free, so this lists first and fetches only what it has not taken before.
`already_taken` comes from the server and is per key, which means this stays correct even
if you lose your local state — you will not be billed twice for the same article.
"""
import argparse
import json
import os
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = os.environ.get("BLINK_WIRE_BASE", "https://wire.blinkhub.net")
KEY = os.environ.get("BLINK_WIRE_KEY", "")


def call(path, **params):
    url = f"{BASE}{path}"
    if params:
        url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    req = urllib.request.Request(url, headers={"X-Api-Key": KEY})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read()), dict(r.headers)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            code = json.loads(body)["error"]["code"]
        except Exception:
            code = str(e.code)
        raise SystemExit(f"HTTP {e.code} ({code}) on {path}") from None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", default="us")
    ap.add_argument("--since", help="ISO 8601; only items received after this")
    ap.add_argument("--limit", type=int, default=20, help="1-100")
    ap.add_argument("--out", default="./articles")
    ap.add_argument("--dry-run", action="store_true", help="list only, fetch nothing")
    args = ap.parse_args()

    if not KEY:
        raise SystemExit("set BLINK_WIRE_KEY")

    listing, _ = call("/api/wire/v1/articles", market=args.market,
                      limit=args.limit, since=args.since)
    items = listing["items"]
    fresh = [i for i in items if not i["already_taken"]]
    print(f"{listing['count']} available, {len(fresh)} not yet taken", file=sys.stderr)

    if args.dry_run:
        for i in items:
            mark = " " if i["already_taken"] else "*"
            print(f"{mark} {i['id']:>8}  {i['source'] or '-':<28} {i['headline'][:70]}")
        return

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    spent = 0
    for i in fresh:
        doc, headers = call(f"/api/wire/v1/articles/{i['id']}", market=args.market)
        (out / f"{i['id']}.json").write_text(
            json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
        charged = int(headers.get("X-Wire-Credits-Charged", 0))
        spent += charged
        print(f"saved {i['id']} (charged {charged}, balance "
              f"{headers.get('X-Wire-Credits-Balance', '?')})", file=sys.stderr)

    print(f"done — {len(fresh)} articles, {spent} charged", file=sys.stderr)


if __name__ == "__main__":
    main()
