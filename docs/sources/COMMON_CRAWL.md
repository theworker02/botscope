# Common Crawl

**Status:** ACTIVE (zero-auth)

## What it measures

Published Common Crawl index catalog (`collinfo.json`): crawl ids, time windows, CDX API endpoints.

## Who operates it

Common Crawl Foundation — https://commoncrawl.org/

## How BotScope accesses it

HTTPS GET `https://index.commoncrawl.org/collinfo.json` — no API key.

## Authentication

NONE

## License

Public Common Crawl data; review Common Crawl terms for redistribution of derived datasets.

## Refresh frequency

Monthly crawls; BotScope caches catalog (~10 minutes default).

## What BotScope uses it for

- Sampling-frame / crawl-window discovery
- Longitudinal web corpus context
- CDX endpoint listing

## What BotScope DOES NOT use it for

- “Percentage of Internet traffic that is bots”
- Substituting for HTTP edge telemetry

## Known limitations

Crawler politeness and schedule bias; English/web skew; not a traffic census.
