# Feature matrix

Labels reflect repository reality for BotScope **v2.0.0**.

| Feature | Status | Module | Notes |
|---------|--------|--------|-------|
| Offline Analyzer API | IMPLEMENTED | `botscope.api` | Includes query re-exports; geo/flows/behavior in report |
| Rules + identity classifier | IMPLEMENTED | `botscope.classify`, `identity` | |
| ML classifier (`feature_logistic_v1`) | IMPLEMENTED | `botscope.classify.ml` | Default on; never overrides verified identity |
| Combined/common log ingest | IMPLEMENTED | `botscope.ingest` | |
| Session store (.bscope) | IMPLEMENTED | `botscope.storage` | + workspace sidecar, summary/list |
| Reports JSON/MD/HTML/CSV | IMPLEMENTED | `botscope.reports` | |
| Multi-format export job | IMPLEMENTED | `botscope.export` | Unified ExportJob + CLI |
| Privacy transforms | IMPLEMENTED | `botscope.privacy` | |
| Network client (OFF default) | IMPLEMENTED | `botscope.network` | |
| Signatures packs | IMPLEMENTED | `botscope.signatures` | |
| CLI | IMPLEMENTED | `botscope.cli` | live/capture/flows/geo/eval/federation/hello/access/… |
| Desktop Observatory GUI | IMPLEMENTED | `botscope.gui` | Native Qt/PySide6 (not a website) |
| Global Observatory | IMPLEMENTED | `botscope.sources`, `gui.global_observatory` | Zero-auth federation; Radar OPTIONAL_AUTH |
| Internet estimate headline | IMPLEMENTED | `botscope.estimation.internet` | Opens with ≥2 weighted traffic shares + uncertainty |
| Observatory v2 workstation | IMPLEMENTED | `botscope.gui` | Save/load/history, compare, query, virtualized events, workspace, export, annotations |
| Streaming snapshots | IMPLEMENTED | `botscope.live`, `gui.streaming` | Bound Hz; GUI ≠ per-event |
| Authorized live log-tail | IMPLEMENTED | `botscope.live`, `gui.workers` | Bound snapshots + CLI |
| Live SessionStore persist | IMPLEMENTED | `botscope.live.persist` | Append-only batches |
| Multi-sensor fan-in | IMPLEMENTED | `botscope.live.fanin` | Local sensors only |
| Threshold alerts | IMPLEMENTED | `botscope.live.alerts` | Local measurement rules |
| Offline PCAP ingest | IMPLEMENTED | `botscope.ingest.pcap` | Classic pcap stdlib; pcapng via scapy |
| Live interface sniff | IMPLEMENTED | `botscope.capture.live` | Needs `botscope[capture]` + auth + OS perms |
| Analysis Workspace | IMPLEMENTED | `botscope.workspace` | `workspace.json` in `.bscope` |
| Session history index | IMPLEMENTED | `botscope.history` | Local MRU JSON |
| Timeline bucketing | IMPLEMENTED | `botscope.timeline` | Multi-resolution |
| Confidence calibration metrics | IMPLEMENTED | `botscope.calibration` | Brier/ECE; needs labels |
| Classification eval | IMPLEMENTED | `botscope.eval` | P/R/F1 + confusion |
| Geo aggregates + offline table | IMPLEMENTED | `botscope.geo` | Coarse tags + IP≠person caveat |
| ASN offline table | IMPLEMENTED | `botscope.asn` | Optional local CSV/JSON |
| Enrich composer | IMPLEMENTED | `botscope.enrich` | ASN/geo/static + optional rDNS |
| Demo corpus | IMPLEMENTED | `botscope.demo` | Synthetic |
| First-run hello | IMPLEMENTED | `botscope.onboarding`, `cli` | `botscope hello` — offline demo summary; `--json` / `--keep-session` |
| Ease-of-access checklist | IMPLEMENTED | `botscope.onboarding`, `cli` | `botscope access` + richer `botscope quickstart` |
| Labeled eval fixtures | IMPLEMENTED | `datasets/fixtures` | Mini labeled JSONL |
| Provenance inspector | IMPLEMENTED | `botscope.provenance` | |
| Quality scorecard | IMPLEMENTED | `botscope.quality` | |
| Session compare | IMPLEMENTED | `botscope.compare` | GUI Compare tab |
| Classifier compare | IMPLEMENTED | `botscope.compare` | GUI panel |
| Research export + citation | IMPLEMENTED | `botscope.research` | |
| Safe query filter | IMPLEMENTED | `botscope.query` | GUI + CLI + Python |
| Annotations | IMPLEMENTED | `botscope.annotations` | GUI panel |
| Diagnostics / doctor bundle | IMPLEMENTED | `botscope.diagnostics` | |
| Plugin SDK | IMPLEMENTED | `botscope.plugins.sdk` | |
| Capability registry | IMPLEMENTED | `botscope.capabilities` | |
| Bot Cards | IMPLEMENTED | `botscope.botcard` | |
| Measurement manifests | IMPLEMENTED | `botscope.manifests` | |
| Notebook | EXPERIMENTAL | `botscope.notebook` | load/filter/save |
| Capture helpers | IMPLEMENTED | `botscope.capture` | |
| Behavior profiles | IMPLEMENTED | `botscope.behavior` | Entropy, automation fraction, bot-like score |
| Flow aggregation | IMPLEMENTED | `botscope.flows` | |
| Estimation | IMPLEMENTED | `botscope.estimation` | Local shares + gated Internet headline |
| Dataset helpers | IMPLEMENTED | `botscope.datasets` | + labeled fixtures |
| Microbenchmarks | IMPLEMENTED | `benchmarks/` | Run locally; no invented timings |

Use `botscope features` for the machine-readable registry.
