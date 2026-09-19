# Installation

Status: **IMPLEMENTED**

Requires Python 3.10+.

```bash
git clone https://github.com/theworker02/botscope.git
cd botscope
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -e ".[gui,dev]"
```

For CLI-only work without the Observatory, `pip install -e ".[dev]"` is enough.

Extras:

| Extra | Purpose |
|-------|---------|
| `gui` | PySide6 + pyqtgraph desktop Observatory |
| `capture` | scapy (authorized live interface sniff) |
| `network` | httpx/cryptography for opt-in network client |
| `ml` | numpy/sklearn classifier hooks |
| `analytics` | duckdb/pyarrow |
| `all` | everything |

Verify:

```bash
botscope doctor
botscope demo --output demo_analysis.bscope
pytest
```

Desktop app: `botscope gui` (see [../GUI.md](../GUI.md)). Fast path: [QUICKSTART.md](QUICKSTART.md).
