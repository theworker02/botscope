# Phase III — Global Observatory

**Status:** FOUNDATION IMPLEMENTED  
**Canonical UI:** existing PySide6 Observatory — Global tab added (not a replacement)

## Shipped

- Source federation (`botscope.sources`): registry, cache+receipts, health, adapters
- Zero-auth: Common Crawl collinfo, Google crawler IP ranges (live-verified 2026-09-18)
- Optional auth: Cloudflare Radar (token via env; never shipped)
- Estimation: `population_reliability_v1` opens **INTERNET BOT TRAFFIC ESTIMATE** when ≥2 weighted traffic shares + uncertainty qualify; otherwise MULTI-SOURCE OBSERVATIONS
- Local sensor adapter emits `automated_share` from session stats when provided
- GUI: Global Observatory panel with toggles, health board, raw source table, explainer
- Docs: `docs/sources/*`, `docs/research/GLOBAL_ESTIMATION.md`

## Still prohibited

- Equal-weight averaging of heterogeneous source rates
- Auth bypass for Radar
- Synthetic global dashboard numbers / invented prevalences
