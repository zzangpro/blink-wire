# BLINK Wire — news content API

A pull API for publishers who want Korean and US public-sector news without running a
local desk. You call the endpoint when you want material; each full article you take is
metered once. Documents come back as [IPTC ninjs 2.1](https://www.iptc.org/std/ninjs/).

**Base URL** `https://wire.blinkhub.net` · **Auth** `X-Api-Key` header
· **Details and access** <https://blinkhub.net/en/korean-news-api>

```bash
curl -H "X-Api-Key: $BLINK_WIRE_KEY" \
  "https://wire.blinkhub.net/api/wire/v1/articles?limit=20"
```

## What is in it

| Feed | `market` | Status | What it is |
|---|---|---|---|
| United States | `us` | **Live** | Over 4,000 government releases cleared for distribution — NASA, the White House, federal departments, state governors, city offices. Growing daily. |
| Korea | — | **By arrangement** | Announcements from roughly 240 Korean public bodies. Not open self-serve: the Korean side runs under distribution contracts, so we check the rights for your intended use before enabling it on your key. |

## Endpoints

| | Billed | |
|---|---|---|
| `GET /api/wire/v1/health` | — | Liveness. No key needed. |
| `GET /api/wire/v1/me` | free | Your account, per-article rate, remaining balance. |
| `GET /api/wire/v1/articles` | **free** | What is available. Headlines and metadata, no body. |
| `GET /api/wire/v1/articles/{id}` | **per article** | The full ninjs document. |

### Listing

`GET /api/wire/v1/articles?market=us&limit=20&since=2026-09-01T00:00:00`

`limit` is 1–100 (default 20). `since` filters on `received_at`, so a scheduled job can ask
only for what appeared after its last run.

```json
{
  "market": "us",
  "count": 1,
  "items": [
    {
      "uri": "urn:blink:wire:us:48211",
      "id": "48211",
      "headline": "NASA Selects Instruments for Lunar Surface Mission",
      "description_text": null,
      "source": "NASA",
      "versioncreated": "2026-09-25T22:10:04.120000+09:00",
      "has_image": true,
      "body_chars": 4180,
      "already_taken": false
    }
  ]
}
```

`already_taken` tells you whether this key has fetched that article before — if it has,
fetching it again is free.

### Fetching one

`GET /api/wire/v1/articles/{id}?market=us&lang=en`

Returns a ninjs 2.1 document, plus two response headers:

```
X-Wire-Credits-Charged: 1
X-Wire-Credits-Balance: 415
```

Bodies are cleaned of site furniture before they reach you (newsletter prompts, share rows,
duplicated blocks) and image URLs are rewritten to public addresses, so nothing arrives
pointing at an internal host. Non-standard fields are kept under `x_blink` so a standards
compliant consumer can ignore them.

## Billing

- **Listing is free.** You should be able to see what exists before paying for any of it.
- **A full fetch is charged once.** The first time this key takes a given article.
- **Re-fetching is free.** After a crash, during a re-index, from a second system — no second charge.
- **Nothing is charged for an article we refuse to serve.** The quality gate runs before billing.
- No subscription and no minimum term. Rate depends on volume and intended use; ask.

## Errors

All errors share one shape:

```json
{ "error": { "code": "insufficient_credits", "message": "..." } }
```

| HTTP | `code` | |
|---|---|---|
| 401 | `unauthorized` | Missing, unknown or suspended key. |
| 400 | `unknown_market` | That `market` is not enabled for you. |
| 402 | `insufficient_credits` | Balance is below the per-article rate. |
| 404 | `not_found` | No such article, or it is not cleared for distribution. |
| 409 | `not_distributable` | Failed the quality gate. **Not billed.** |
| 500 | `internal_error` | Transient. Retry. |

## Examples

- [`examples/fetch.py`](examples/fetch.py) — Python, standard library only
- [`examples/fetch.mjs`](examples/fetch.mjs) — Node 18+, no dependencies
- [`openapi.yaml`](openapi.yaml) — OpenAPI 3.1 description of the whole API

Both examples do the same thing: list what is new since a timestamp, then fetch only the
articles this key has not taken before.

## Getting a key

Email **contact@blinkhub.net** with your organisation, what you publish and which feed you
want. There is no self-serve signup yet — keys are issued per organisation.

Full write-up: <https://blinkhub.net/en/korean-news-api>

## Licence

The code in this repository is MIT (see [LICENSE](LICENSE)). The articles the API serves are
not — they are licensed to you under your own agreement, and the `usageterms` field on every
document states the terms that apply.
