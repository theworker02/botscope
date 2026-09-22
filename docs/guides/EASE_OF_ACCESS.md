# Ease of access — first-hour guide

Status: **IMPLEMENTED** (matches `botscope hello`, `botscope access`, `botscope quickstart`)

This guide is for new users and acquisition evaluators who want a measurable result quickly, without accounts, API keys, or network contribution.

Network contribution stays **OFF by default**. Demo shares are **synthetic** — not Internet-wide census metrics.

## Goals for the first hour

1. Install BotScope
2. Produce a labeled demo analysis offline (`botscope hello`)
3. Know where local data lives
4. Optionally open the desktop Observatory or analyze an authorized log
5. Know how to keep network paths disabled

## 0–5 minutes: install

**CLI / library only:**

```bash
pip install botscope
```

**With native desktop Observatory (Qt):**

```bash
pip install 'botscope[gui]'
```

**All optional extras** (capture, network client, ML, analytics, GUI, dev):

```bash
pip install 'botscope[all]'
```

From a git clone (contributors):

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e '.[gui,dev]'
```

Verify the environment:

```bash
botscope doctor
```

## 5–10 minutes: first result (`hello`)

```bash
botscope hello
```

What this does:

- Runs the bundled synthetic demo corpus end-to-end
- Works **without GUI**, **without network**, and **without API keys**
- Prints event count, automation / human / unknown fractions, top categories, and next steps
- Always labels output as **DEMO DATA**

Useful options:

```bash
botscope hello --json
botscope hello --keep-session hello.bscope
```

`--keep-session` writes a local `.bscope` folder you can `botscope open` or load in the GUI.

Print the same path any time:

```bash
botscope quickstart
botscope access
```

## 10–20 minutes: understand the surfaces

| Command | Purpose |
|---------|---------|
| `botscope hello` | Offline first-run demo summary |
| `botscope access` | Ease-of-access checklist (install, data dirs, privacy) |
| `botscope quickstart` | Richer install → hello → demo → analyze → GUI → doctor → Global |
| `botscope demo` | Full demo session to a `.bscope` path |
| `botscope analyze PATH` | Authorized log / PCAP analysis |
| `botscope gui` / `botscope` | Native Qt Observatory |
| `botscope doctor` | Environment / policy diagnostics |
| `botscope federation` | Global Observatory public-source snapshot |

## Where data lives

All of the following are **local** unless you explicitly enable network features:

| Kind | Location |
|------|----------|
| Config (e.g. network.json) | platformdirs user config for `botscope` |
| HTTP source cache | platformdirs user cache for `botscope` |
| UX settings / recents | `~/.config/botscope` (or `%LOCALAPPDATA%\BotScope` on Windows); override with `BOTSCOPE_UX_DIR` |
| Analysis sessions | Paths you pass (`--output`, `--keep-session`) — `.bscope` folders on disk you control |

Print resolved paths:

```bash
botscope access
# or machine-readable:
botscope access --json
```

## Desktop Observatory

```bash
botscope gui
# or simply:
botscope
```

- **Demo** loads the synthetic corpus (DEMO DATA banner)
- **Open** / drag-and-drop for authorized logs, PCAPs, or `.bscope` sessions
- **Global** federates zero-auth public sources; Cloudflare Radar token in Settings is optional and never required for local analysis

GUI map: [../GUI.md](../GUI.md).

## Analyze your own authorized traffic

Only analyze systems and traffic you own or have permission to measure.

```bash
botscope analyze /path/to/access.log --output my.bscope
botscope query my.bscope --expr 'classification eq "AI CRAWLER"'
botscope report my.bscope --format markdown --output report.md
```

Python:

```python
from botscope import Analyzer

result = Analyzer().analyze("access.log")
print(result.automation_fraction)
print(result.stats.by_category)
```

## Privacy defaults

- Network **contribution**: OFF (`enabled=false` in local network config)
- Local analysis: no cloud profile required
- Query redaction: ON by default in Observatory settings
- IP hashing / truncation: OFF until you enable them
- Optional Cloudflare Radar token: stored locally; leave empty for fully offline local work

## How to disable network forever (practical)

1. Do **not** install the `[network]` extra unless you need the opt-in client
2. Leave contribution disabled (default) — never flip `enabled` in network config
3. Leave the Cloudflare Radar token empty
4. Set `BOTSCOPE_NO_IDENTITY_RANGES=1` to skip published crawler-range fetches during analyze
5. Prefer `botscope hello` / offline demo paths for evaluation without egress
6. Run `botscope doctor` and confirm contribution / policy checks stay OFF

`botscope hello` already uses identity ranges disabled so the first-run path does not attempt range fetches.

## Global Observatory (optional in the first hour)

The product’s Internet-wide census story lives on the GUI **Global** page and `botscope federation`. Public panels are zero-auth; CDN estimates from Cloudflare Radar are optional. Local KPIs remain dataset-scoped — do not treat a single log’s automation fraction as a worldwide rate.

## Buyer / diligence path

Acquisition briefing: [../../ACQUISITION.md](../../ACQUISITION.md)  
Buyer demo script: [../acquisition/BUYER_DEMO.md](../acquisition/BUYER_DEMO.md)

Minimal evaluator loop:

```bash
pip install botscope
botscope doctor
botscope hello
botscope access
```

## Next reading

| Goal | Doc |
|------|-----|
| Install extras | [INSTALLATION.md](INSTALLATION.md) |
| Short quickstart | [QUICKSTART.md](QUICKSTART.md) |
| Feature matrix | [../../FEATURES.md](../../FEATURES.md) |
| Query language | [../QUERY.md](../QUERY.md) |
| Limitations | [../research/LIMITATIONS.md](../research/LIMITATIONS.md) |
| Troubleshooting | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
