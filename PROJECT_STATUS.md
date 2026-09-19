# Project status

**Version:** 2.0.0  
**Last update:** 2026-09-18

## What works today

- Offline analysis of combined/common web logs via `Analyzer` and `botscope analyze`
- Bundled synthetic demo via `botscope demo` (always labeled DEMO)
- Evidence-backed rule/identity classification with UNKNOWN as a valid outcome
- Bundled ML classifier (`feature_logistic_v1`, default on) — never overrides verified identity
- Local `.bscope` sessions (save/load from GUI), reports (incl. geo/flows/behavior), privacy transforms, Analysis Workspace
- Native Qt **Observatory v2**: virtualized events, shared query language, compare, annotations, export, history
- **Live workstation**: authorized log-tail + interface sniff, multi-sensor fan-in, threshold alerts, continuous `.bscope` persistence
- Offline PCAP ingest + geo/ASN offline tables + enrich composer (optional rDNS via `BOTSCOPE_RDNS`)
- **Internet estimate**: `population_reliability_v1` opens `INTERNET BOT TRAFFIC ESTIMATE` when ≥2 weighted traffic shares + uncertainty qualify
- Behavior profiles (IMPLEMENTED): entropy, automation fraction, bot-like score
- Research tooling: provenance, quality, compare, research bundles, doctor, plugin SDK, calibration/eval/timeline
- Rich CLI: `live-tail`, `capture --iface --authorize`, `flows`, `behavior`, `geo`, `eval`, `federation`, `export`, …

## Caveats (honest, not “missing”)

- Internet headline needs ≥2 independent *traffic-share* sources (catalog-only sources never invent a rate)
- ML scores are model probabilities — not population prevalence
- Behavior profiles are observational features, not attribution proof
- Geo/ASN depend on user-supplied offline tables (no MaxMind shipped)

## What is intentionally not claimed

- No equal-weight average of heterogeneous sources
- No fabricated benchmarks
- Network contribution remains OFF by default
- Sensor ● LIVE only when an authorized live worker is actually running

## Regression

Frozen Observatory shell baseline: **20 tests**. New tests raise the floor — see
`docs/development/REGRESSION_BASELINE.md`.
