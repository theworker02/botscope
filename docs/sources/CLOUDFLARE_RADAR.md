# Cloudflare Radar

**Status:** OPTIONAL_AUTH_SOURCE / AUTH_REQUIRED until user token

## What it measures

Aggregated HTTP traffic dimensions from Cloudflare’s network, including botClass `LIKELY_AUTOMATED` and `LIKELY_HUMAN`.

## Who operates it

Cloudflare — https://radar.cloudflare.com/

## How BotScope accesses it

Official Radar API: `https://api.cloudflare.com/client/v4/radar/` with user Bearer token.

BotScope only calls read endpoints such as:

`GET /client/v4/radar/http/summary/bot_class`

## Authentication (minimal token — do NOT grant “everything”)

**Optional** — only needed for CDN-wide Radar estimates. Not required for your server logs.

### Create the token (dashboard)

1. Open [Cloudflare API Tokens](https://dash.cloudflare.com/profile/api-tokens)
2. **Create Token** → **Create Custom Token** (do not use Edit zone DNS / Edit Cloudflare Workers templates)
3. **Token name:** e.g. `BotScope Radar Read`
4. **Permissions** — add exactly one row:
   - Type: **Account**
   - Permission group: **Radar**
   - Level: **Read**
5. **Account Resources:**
   - Include → **Specific account** → pick your Cloudflare account
   - (If the UI only offers “All accounts” and you have one account, that is fine)
6. **Zone Resources:** leave empty / not applicable — Radar is account-scoped, not zone-scoped
7. Continue → Create Token → copy once into BotScope **Settings → Cloudflare Radar (optional bonus)**

### What NOT to select

- Do **not** grant Zone DNS Edit, Workers Edit, Account Settings Edit, Billing, etc.
- Do **not** use “Edit zone DNS” or other broad templates
- BotScope never needs write access

Official Cloudflare first-request docs:  
https://developers.cloudflare.com/radar/get-started/first-request/

## License / terms

Cloudflare API / Radar terms apply to the token holder.

## What BotScope uses it for

- SOURCE-REPORTED Cloudflare-observed automated/human HTTP shares
- Optional enrichment of Global Observatory when connected

## What BotScope DOES NOT use it for

- Claiming “X% of the Internet is bots”
- Operating Radar without credentials
- Accessing your zones, DNS, Workers, or billing

## Known limitations

Large but non-random slice of Internet activity; Cloudflare classification methodology; customer/edge bias.
