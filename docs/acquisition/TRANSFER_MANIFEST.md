# Transfer Manifest — BotScope

**Date:** 2026-09-21

| Asset | Category | Notes |
|-------|----------|-------|
| repository | TRANSFERABLE | github.com/theworker02/botscope |
| source code (original) | TRANSFERABLE | Subject to historical Apache grants |
| PyPI package botscope | TRANSFERABLE_WITH_CONSENT | Trusted Publishing / PyPI ownership transfer |
| datasets/demo + fixtures | TRANSFERABLE | Synthetic/hand-labeled; still confirm intent |
| operator IP list caches | PUBLIC/THIRD-PARTY | Not BotScope-owned; operator terms apply |
| Cloudflare Radar derived metrics | REQUIRES_PERMISSION | API/terms; token is buyer's |
| brand BotScope | TRANSFERABLE_WITH_CONSENT | Registration UNKNOWN |
| secrets | NONTRANSFERABLE | Rotate only |

## Credentials migration checklist (no secrets committed)

- [ ] Inventory GitHub secrets / Actions secrets
- [ ] Inventory cloud API tokens (Cloudflare, etc.)
- [ ] Inventory package registry tokens
- [ ] Inventory signing keys
- [ ] Rotate all of the above at closing — **ROTATE_IMMEDIATELY** if any exposure suspected
- [ ] Buyer creates replacement secrets in buyer-controlled accounts

**NEVER commit credentials.**
