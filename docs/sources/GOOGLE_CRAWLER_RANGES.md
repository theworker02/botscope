# Google Crawler IP Ranges

**Status:** ACTIVE (zero-auth identity)

## What it measures

Published CIDR prefixes for Google common (and optionally special) crawlers.

## Operator

Google — crawler verification documentation.

## Access

HTTPS JSON:

- `https://developers.google.com/static/crawling/ipranges/common-crawlers.json`
- `https://developers.google.com/static/crawling/ipranges/special-crawlers.json`

## Authentication

NONE

## BotScope uses

Supporting evidence for identity verification during **analyze** (and live classify),
not only Global Observatory. Cache-first via `HttpSourceCache`; opt out with
`botscope analyze --no-identity-ranges` or `BOTSCOPE_NO_IDENTITY_RANGES=1`.

Both **common** and **special** crawler JSON files are loaded into `PublishedRangeIndex`.

## BotScope does not use

User-Agent string alone as VERIFIED identity.
