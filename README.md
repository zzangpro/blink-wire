# BlinkHub Wire — government news API and MCP server

Government press releases from six markets, ready to run: the United States, Korea, the
United Kingdom, the European Union, New Zealand and Australia. Pull them over a REST API as
[IPTC ninjs 2.1](https://www.iptc.org/std/ninjs/), or connect an AI assistant such as Claude
through the **MCP server** and let it search and read them for you.

**Base URL** `https://wire.blinkhub.net` · **MCP** `https://wire.blinkhub.net/mcp`
· **Auth** `X-Api-Key` header · **Free tier** 100 full articles a month
· **Docs** <https://blinkhub.net/en/korean-news-api>

```bash
curl -H "X-Api-Key: $BLINK_WIRE_KEY" \
  "https://wire.blinkhub.net/api/wire/v1/articles?market=gb&limit=20"
```

## What is in it

| Feed | `market` | Language | What it is | Source licence |
|---|---|---|---|---|
| United States | `us` | en | Edited releases from federal agencies (NASA, the White House, federal departments) and some state and city offices | Federal works are public domain; credit the agency |
| Korea | `kr` | ko | Korean-language releases from Korean central and local government bodies, roughly 1,600–2,500 per weekday. Only recent days are online. | Credit the issuing body |
| United Kingdom | `gb` | en | GOV.UK press releases, rewritten as news copy | Open Government Licence v3.0 |
| European Union | `eu` | en | European Commission press releases, rewritten as news copy | CC BY 4.0 |
| New Zealand | `nz` | en | New Zealand Government releases, rewritten as news copy | CC BY 4.0 |
| Australia | `au` | en | Prime Minister of Australia media releases, rewritten as news copy | CC BY 4.0 (excludes the Coat of Arms and photos) |

Every document carries the attribution line it needs in `copyrightnotice`. Sources whose
terms do not allow commercial redistribution are left out of the feed.

## Getting a key

1. Register your publication at <https://blinkhub.net/en/publishers/join> (free account).
2. In the portal, open **Wire**: add your site, fill in your publication details, agree to the
   terms and verify the site (a meta tag or a text file).
3. We review and approve the publication, and you are emailed when it is approved.
4. Copy your key from the portal. It is shown once; you can rotate it from the same screen.

The free tier covers 100 full articles a month. For higher volumes, write to
**contact@blinkhub.net**.

## Use it from an AI assistant (MCP)

The MCP server speaks Streamable HTTP at `https://wire.blinkhub.net/mcp` and takes your key in
the `X-Api-Key` header (or `Authorization: Bearer <key>`).

**Claude Code**

```bash
claude mcp add --transport http blinkhub-wire https://wire.blinkhub.net/mcp \
  --header "X-Api-Key: $BLINK_WIRE_KEY"
```

**Any client that reads an `mcpServers` config**

```json
{
  "mcpServers": {
    "blinkhub-wire": {
      "type": "http",
      "url": "https://wire.blinkhub.net/mcp",
      "headers": { "X-Api-Key": "YOUR_KEY" }
    }
  }
}
```

Then ask in plain language — *"Find this week's UK government announcements on energy and
summarise the top one, with the attribution line."*

| Tool | Uses quota | What it does |
|---|---|---|
| `list_markets` | no | The six markets, their language, content and licence |
| `search_articles` | no | Keyword search over recent articles in one market (headline, summary, source agency, time, id) |
| `get_article` | 1 article, first time only | Full text, source agency, original link and the attribution line |
| `account_status` | no | Your plan, monthly quota and usage |

Search Korean articles with Korean keywords (for example `반도체`, `수출`).

Also listed in the [official MCP Registry](https://registry.modelcontextprotocol.io) as
`net.blinkhub/wire`.

## REST endpoints

| | Billed | |
|---|---|---|
| `GET /api/wire/v1/health` | — | Liveness. No key needed. |
| `GET /api/wire/v1/me` | free | Your account, plan, quota and usage. |
| `GET /api/wire/v1/articles` | **free** | What is available. Headlines and metadata, no body. |
| `GET /api/wire/v1/articles/{id}` | **per article** | The full ninjs document. |
| `POST /api/wire/v1/publications` | free | Optional: tell us where you published a story you took. |
| `GET /api/wire/v1/publications` | free | Your reported publications. |

### Listing

`GET /api/wire/v1/articles?market=gb&limit=20&since=2026-10-01T00:00:00Z`

`market` defaults to `us`. `limit` is 1–100 (default 20). `since` returns only what appeared
after that time, so a scheduled job can ask for what is new since its last run.

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

`GET /api/wire/v1/articles/{id}?market=us`

Returns a ninjs 2.1 document. Bodies are cleaned of site furniture (newsletter prompts, share
rows, duplicated blocks) and image URLs point at public addresses. Non-standard fields are kept
under `x_blink` so a standards-compliant consumer can ignore them. Korean articles embargoed
by the issuing body stay hidden until the embargo time.

## Billing

- **Listing and searching are free.** See what exists before you take any of it.
- **A full fetch counts once** — the first time this key takes a given article.
- **Re-fetching is free.** After a crash, during a re-index, from a second system.
- **Nothing is counted for an article we refuse to serve.** The quality gate runs first.

## Errors

All errors share one shape:

```json
{ "error": { "code": "quota_exceeded", "message": "..." } }
```

| HTTP | `code` | |
|---|---|---|
| 401 | `unauthorized` | Missing, unknown or suspended key. |
| 400 | `unknown_market` | Unknown `market`. |
| 402 | `quota_exceeded` | Free tier: this month's quota is used up. |
| 402 | `insufficient_credits` | Paid tier: balance is below the per-article rate. |
| 404 | `not_found` | No such article, or it is not available for distribution. |
| 409 | `not_distributable` | Failed the quality gate. **Not counted.** |
| 500 | `internal_error` | Transient. Retry. |

## WordPress

The [BlinkHub Wire Importer](https://wordpress.org/plugins/blinkhub-wire-importer/) plugin
imports articles into WordPress on a schedule and reports publications back automatically.

## Examples

- [`examples/fetch.py`](examples/fetch.py) — Python, standard library only
- [`examples/fetch.mjs`](examples/fetch.mjs) — Node 18+, no dependencies
- [`openapi.yaml`](openapi.yaml) — OpenAPI 3.1 description of the REST API

Both examples list what is new since a timestamp, then fetch only the articles this key has
not taken before. Pass `--market gb` (or any market code) to read another feed.

## Licence

The code in this repository is MIT (see [LICENSE](LICENSE)). The articles are not: each
document's `copyrightnotice` and `usageterms` fields state the terms that apply.
