# Source Research (2026-09-18)

Fresh verification against official documentation and live retrieval.

## Selection gate applied

| Source | REAL | ACCESS | DOCS | LICENSE | PARSER | PROVENANCE | LIMITS | NO BYPASS | Decision |
|--------|------|--------|------|---------|--------|------------|--------|-----------|----------|
| Common Crawl collinfo | PASS | PASS (HTTPS, no auth) | PASS | Reviewed (public dataset) | PASS | PASS | PASS | PASS | **ACTIVE** |
| Google crawler IP JSON | PASS | PASS | PASS | Operator-published | PASS | PASS | PASS | PASS | **ACTIVE** |
| Cloudflare Radar | PASS | AUTH required | PASS | API terms | PARTIAL | PASS | PASS | PASS | **OPTIONAL_AUTH / AUTH_REQUIRED** |

## Common Crawl

- Operator: Common Crawl Foundation
- Verified endpoint: `https://index.commoncrawl.org/collinfo.json` (HTTP 200, 127 crawls on 2026-09-18)
- Latest crawl at verification: `CC-MAIN-2026-34`
- Data also at `https://data.commoncrawl.org/` without AWS account
- **Perspective:** WEB CRAWL DATASET
- **Does NOT support:** Internet bot-traffic percentage

## Google crawler IP ranges

- Verified: `https://developers.google.com/static/crawling/ipranges/common-crawlers.json`
- 317 prefixes; `creationTime` present
- Identity evidence only; UA alone insufficient

## Cloudflare Radar

- Docs: https://developers.cloudflare.com/radar/
- API: `https://api.cloudflare.com/client/v4/radar/` with `Authorization: Bearer`
- botClass: `LIKELY_AUTOMATED` / `LIKELY_HUMAN`
- **BotScope never ships tokens**
- Population: Cloudflare-observed HTTP — not the Internet

## Rejected / deferred

- Scraping authenticated Radar web UI: **REJECTED**
- Invented undocumented endpoints: **REJECTED**
- Averaging provider shares into “Internet %”: **REJECTED** until estimation gate passes
