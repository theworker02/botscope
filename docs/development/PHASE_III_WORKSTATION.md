# Phase III / Observatory v2 — Measurement Workstation

**Status:** v2 DELIVERED — live log-tail + interface sniff + persist + fan-in + alerts  
**Canonical UI:** existing PySide6 Observatory (`botscope.gui`) — **do not replace**

## Goal

Evolve the Observatory from a strong dataset viewer into a serious
network-measurement workstation by **extending** the shell.

## Non-goals

- No web UI / browser shell
- No GUI framework migration
- No deletion of Observatory panels that already work
- No fabricated live rates or marketing benchmarks

## v2 deliverables

| # | Deliverable | Status |
|---|-------------|--------|
| 1 | Persistent `.bscope` save / load / history | IMPLEMENTED |
| 2 | Session comparison tab | IMPLEMENTED |
| 3 | Shared query engine (GUI + CLI + Python) | IMPLEMENTED |
| 4 | Virtualized events (`QAbstractTableModel`) | IMPLEMENTED |
| 5 | Analysis Workspace persistence | IMPLEMENTED |
| 6 | StreamingAggregator + bounded snapshots | IMPLEMENTED |
| 7 | Authorized live log-tail → dashboard | IMPLEMENTED |
| 8 | Live SessionStore persistence | IMPLEMENTED |
| 9 | Multi-sensor fan-in + alert rules | IMPLEMENTED |
| 10 | Live interface sniff (scapy + auth) | IMPLEMENTED |
| 11 | Internet estimate gate (`population_reliability_v1`) | IMPLEMENTED |
| 12 | Bundled ML classifier (default on) | IMPLEMENTED |

## Thickness packages

| Package | Status |
|---------|--------|
| `botscope.workspace` | IMPLEMENTED |
| `botscope.history` | IMPLEMENTED |
| `botscope.timeline` | IMPLEMENTED |
| `botscope.calibration` | IMPLEMENTED |
| `botscope.live` | IMPLEMENTED |
| `botscope.eval` | IMPLEMENTED |
| `botscope.export` | IMPLEMENTED |
| `botscope.geo` | IMPLEMENTED |
| `botscope.asn` | IMPLEMENTED |
| `botscope.behavior` | IMPLEMENTED |
| `botscope.classify.ml` | IMPLEMENTED |
| `botscope.estimation` | IMPLEMENTED |
| `benchmarks/` | IMPLEMENTED (run locally) |
| `datasets/fixtures/` | IMPLEMENTED |

## Still caveated

- Internet-wide headline requires ≥2 traffic-share sources
- ML probabilities ≠ population prevalence
- Long-run backpressure beyond ring buffer + Hz limits

## Regression

Frozen baseline: **20 tests** — see `docs/development/REGRESSION_BASELINE.md`.
