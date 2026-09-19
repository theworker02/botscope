# Observatory GUI Guide

**Status: IMPLEMENTED** (native desktop, Observatory v2 workstation)  
**Not a website.** BotScope’s Observatory is a local Qt/PySide6 application.

## Launch

```bash
pip install "botscope[gui]"
botscope
# or
botscope gui
```

Zero-config for your own logs: **no account** and **no API key** required. Preferences stay on this machine. Network contribution remains OFF by default.

## What you get

| Area | Purpose |
|------|---------|
| Observatory | Event totals, automated / human-likely / unknown shares, composition ring, Traffic Pulse, timeline, category bars; `apply_snapshot()` for live |
| **Global** | Real public sources (Common Crawl, Google common+special ranges, Bingbot ranges, and related identity feeds); Cloudflare Radar optional; status chips; auto-load on tab |
| Events | **Virtualized** `QAbstractTableModel` + query bar (`botscope.query`) + quick search |
| Classification Inspector | Evidence for/against, identity status, attribution, clipboard copy |
| Dataset Health | Multi-dimension dataset quality scorecard |
| Provenance | Where numbers came from (OBSERVED vs CLASSIFIED) |
| Bot Library | Known signatures vs observed-in-dataset markers |
| Compare | Session-to-session deltas + classifier vs stored labels (no causality) |
| Workspace | Analysis Workspace JSON (filters, denominator, overlays) |
| Annotations | Researcher notes via `AnnotationStore` (not evidence) |
| Exports | Multi-format report builder (`botscope.export`) |
| History | Recent `.bscope` sessions (local MRU index) |
| Live | Authorized log-tail **or** local interface sniff (scapy); offline PCAP analyze; measured rates only |
| **Settings** | Theme cards (Instrument / High contrast), reduce motion, privacy, welcome prefs, optional Cloudflare Radar token for CDN estimates, Apply theme now |
| Sources | Live registry table (auth mode, type, status, endpoints) |

Screenshots of these pages (demo data) live under [assets/screenshots/](assets/screenshots/).

## Ease of access

- **Open Recent** (File menu) — MRU of logs, PCAPs, and `.bscope` sessions (local only).
- **Drag-and-drop** a log, PCAP, or session folder onto the Observatory window.
- **Welcome** dialog lists recent files and can jump straight to Global Observatory.
- **Quick Export Markdown** (`Ctrl+E` / toolbar) — one-click report without the Export panel.
- **Inspector** — Copy evidence / Copy inspector summary to clipboard.
- **CLI**: `botscope quickstart`, `botscope batch logs/*.log --output-dir out`.

## Sessions

- **File → Save / Save As** writes a portable `.bscope` directory (events, aggregates, versions, `workspace.json`).
- **Open Session** / History browser reloads analyses with workspace state restored.
- Settings can re-open the last session on launch when welcome is disabled.

## Query language

See [QUERY.md](QUERY.md). Same language in GUI, `botscope query`, and Python.

## Live feed

Sensor shows **● LIVE** only while an authorized log-tail worker is running.
Throughput is measured from the aggregator — never placeholder “LIVE” metrics.
Network contribution remains OFF by default.

## Provenance

Every share tile shows a provenance badge. CLASSIFIED shares are never labeled OBSERVED. Demo loads show a **DEMO DATA** banner.

## Denominator

Switch between **% of requests** and **% of bytes** — these are different concepts.

## Optional Cloudflare Radar

Settings includes an optional Cloudflare Radar token field. Leave it blank for normal local-log workflows. Supply *your* Radar Read token only if you want CDN bot/human estimates in Global Observatory. See [sources/CLOUDFLARE_RADAR.md](sources/CLOUDFLARE_RADAR.md).

## Performance

Analysis and live ingest run on background threads. Events use a virtualized table model (no architectural 5k-row hard wall). Prefer structured queries on large corpora.

## Related

- [guides/QUICKSTART.md](guides/QUICKSTART.md)
- [README.md](README.md) (docs index)
- [../README.md](../README.md) (project overview)
