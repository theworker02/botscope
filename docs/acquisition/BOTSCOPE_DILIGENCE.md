# BotScope — Project-Specific Diligence

**Date:** 2026-09-21

## Traffic-data sources

Catalogued in `src/botscope/sources/registry/catalog.py` and `docs/sources/`:
Common Crawl collinfo, Google/Bing/OpenAI/Anthropic/Perplexity/Apple bot IP ranges,
optional Cloudflare Radar, cloud IP ranges, local sensor.

## Source licensing

- Operator-published JSON: review each operator’s terms — **REQUIRES_PERMISSION** / **REQUIRES_LEGAL_REVIEW** for commercial redistribution of cached copies.
- Cloudflare Radar: API token + Cloudflare terms; not transferable as BotScope-owned data.

## API dependencies

- Optional `httpx` network extra; Radar token via env/settings.
- Network contribution off by default per docs.

## Provenance

- Demo logs synthetic (`datasets/demo`).
- Fixtures hand-labeled (`datasets/fixtures`) — not vendor ground truth.

## Bot classification methodology

- Pipeline: ingest → privacy → rules + identity + optional ML → evidence → aggregates.
- UNKNOWN is first-class; ML must not override verified identity.
- Global headline gated on multiple independent traffic-share sources.

## False-positive limitations

- Confidence scores are heuristics, not calibrated prevalence.
- FAQ vs GLOBAL_ESTIMATION messaging conflict noted in audit — treat estimation claims carefully.

## Dataset transferability

- Synthetic/hand-labeled fixtures: likely transferable as original compilation — confirm.
- Operator data: **PUBLIC/THIRD-PARTY** / **REQUIRES_PERMISSION**.
- No MaxMind DB shipped.

## Reproducibility of metrics

- Local demo/doctor path reproducible without tokens.
- Radar-dependent metrics require buyer credentials and are environment-specific.
