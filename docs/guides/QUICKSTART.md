# Quickstart

Status: **IMPLEMENTED** (matches current CLI / GUI)

Zero-config for local logs: no account and no API key required. Network contribution stays OFF by default.

## 1. Install

```bash
git clone https://github.com/theworker02/botscope.git
cd botscope
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -e ".[gui,dev]"
```

See [INSTALLATION.md](INSTALLATION.md) for optional extras (`capture`, `network`, `ml`, `analytics`, `all`).

## 2. Doctor + demo

```bash
botscope doctor
botscope demo --output demo_analysis.bscope
botscope open demo_analysis.bscope
botscope report demo_analysis.bscope --format markdown --output report.md
```

The demo corpus is always labeled **DEMO**. Treat its shares as synthetic, not Internet-wide statistics.

## 3. Desktop Observatory

```bash
botscope gui
# or: botscope
```

- **Demo** — load the bundled synthetic corpus (shows a **DEMO DATA** banner).
- **Open** / drag-and-drop — analyze an authorized access log, PCAP, or `.bscope` session.
- **Global** — zero-auth public sources; optional Cloudflare Radar token in Settings only if you want CDN estimates.

Full GUI map: [../GUI.md](../GUI.md).

## 4. Analyze your own authorized log

```bash
botscope analyze /path/to/access.log --output my.bscope
botscope query my.bscope --expr 'classification eq "AI CRAWLER"'
```

Python:

```python
from botscope import Analyzer

result = Analyzer().analyze("access.log")
print(result.stats.by_category)
print(result.automation_fraction)
```

## Next steps

| Goal | Doc |
|------|-----|
| Query language | [../QUERY.md](../QUERY.md) |
| Provenance & quality | [../tutorials/03_provenance_and_quality.md](../tutorials/03_provenance_and_quality.md) |
| Compare sessions | [../tutorials/04_compare_sessions.md](../tutorials/04_compare_sessions.md) |
| Research export | [../tutorials/05_research_export.md](../tutorials/05_research_export.md) |
| Limitations | [../research/LIMITATIONS.md](../research/LIMITATIONS.md) |
| Runnable scripts | [../../examples/](../../examples/) |

Print the same path from the CLI: `botscope quickstart`.
