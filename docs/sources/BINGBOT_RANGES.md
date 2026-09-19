# Bingbot published IP ranges

**Status:** IMPLEMENTED (zero-auth)  
**Source id:** `bing.bingbot_ip_ranges`  
**Endpoint:** https://www.bing.com/toolbox/bingbot.json

## What BotScope retrieves

Official Microsoft JSON listing IPv4/IPv6 prefixes used by Bingbot. BotScope counts published prefixes and can use range membership as **identity corroboration** — never as proof from User-Agent alone.

## Analyze path

`Analyzer` loads these prefixes (cache-first) into identity checks by default so
Bingbot UA + matching source IP can become **VERIFIED**. Disable with
`--no-identity-ranges` / `BOTSCOPE_NO_IDENTITY_RANGES=1`.

## Limitations

- Does not measure Internet traffic share
- IP match without reverse DNS remains incomplete verification
- Prefer FCrDNS under `search.msn.com` when available

## Related

- Google common + special crawler ranges (`google.crawler_ip_ranges`)
- Identity engine `PublishedRangeIndex` / `load_published_range_index`
