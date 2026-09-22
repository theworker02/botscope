# Changelog

All notable changes to BotScope are documented here. Only features that exist in the repository are listed.

## [Unreleased]

### Added

- **`botscope hello`** — offline first-run demo analysis with friendly summary (`--json`, `--keep-session PATH`); no GUI, network, or API keys required
- **`botscope access`** — ease-of-access checklist (install paths, zero-config claims, data locations, GUI, network-off guidance, doctor)
- Richer **`botscope quickstart`** covering install, hello, demo, analyze, GUI, doctor, Global Observatory, and privacy defaults
- **`botscope.onboarding`** helpers module (testable summary / checklist builders)
- Docs: expanded `ACQUISITION.md`, `docs/guides/EASE_OF_ACCESS.md`, FEATURES/README updates for hello/access

## [2.0.0] — 2026-09-18

Major release: measurement workstation, Global Observatory estimates, bundled ML, and live multi-sensor capture.

### Highlights

- **Observatory v2** workstation (native Qt): virtualized events, query, compare, annotations, export, history, workspace
- Live log-tail + interface sniff with fan-in, alerts, and continuous `.bscope` persistence
- Global Observatory federation + **INTERNET BOT TRAFFIC ESTIMATE** via `population_reliability_v1` (gated on ≥2 weighted traffic shares)
- Bundled ML `feature_logistic_v1` (default on; never overrides verified identity)
- Behavior profiles IMPLEMENTED (entropy, automation fraction, bot-like score)
- Enrich composer (ASN/geo/optional rDNS), flows in reports, full research CLI surface

### Breaking / versioning

- Package version jumps to **2.0.0**
- `RULESET_VERSION` / `MODEL_VERSION` / signature pack version align to 2.0.0
- Classifier confidence notes refer to v2 heuristics/model probabilities (still not population prevalence)

## [0.2.0] — 2026-09-18

Pre-release thickness pass (superseded by 2.0.0 the same day).

- Live persist / fan-in / alerts, enrich, CLI wrappers, Observatory workstation foundations

## [0.1.0] — 2026-09-18

### Added

- Core offline Analyzer pipeline (ingest → privacy → classify → stats → reports → session store)
- Bundled signature packs and rule/identity classification
- CLI: `doctor`, `demo`, `analyze`, `report`, `open`, `compare`, `compare-classifiers`, `citation`, `plugin create|validate`, `features`, `gui`
- Phase II modules: provenance, quality scorecard, compare, research export, query, annotations, diagnostics, plugin SDK, capabilities, botcard, manifests, notebook
- Native Qt Observatory GUI; Global Observatory federation foundations
- Offline PCAP ingest + authorized live interface sniff (`botscope[capture]`)
- Demo corpus + runnable `examples/`
- GitHub community files; network contribution OFF by default
