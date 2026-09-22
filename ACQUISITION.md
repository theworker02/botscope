# Acquisition Brief — BotScope

**Date:** 2026-09-21  
**Status:** Briefing document only. **No acquisition has occurred** by virtue of this file.  
**No valuation** is stated in this document.

## Problem

Operators and researchers lack a transparent, evidence-gated picture of automated Internet traffic versus human-likely traffic. Existing tools often force certainty, conflate a single site’s logs with “the Internet,” or require cloud accounts before a first measurement.

BotScope addresses this with:

- An **Internet-wide census surface** (Global Observatory) that federates public crawler/IP panels and optional CDN estimates
- A **local measurement workstation** (CLI + native Qt Observatory) for authorized logs, sessions, and live capture
- An **UNKNOWN-first** classification posture with provenance badges (OBSERVED / CLASSIFIED / INFERRED)

## Product surfaces

| Surface | How to reach it | Notes |
|---------|-----------------|-------|
| CLI | `botscope <command>` | Headless analyze, hello, doctor, federation, … |
| First-run | `botscope hello` | Offline demo end-to-end; no GUI/network/API keys |
| Ease of access | `botscope access` / `botscope quickstart` | Install paths, data locations, privacy defaults |
| Desktop Observatory | `botscope` or `botscope gui` | Native Qt / PySide6 — not a website |
| Global Observatory | GUI **Global** page / `botscope federation` | Zero-auth public sources; Radar optional |
| Python API | `from botscope import Analyzer` | Same pipeline as CLI |
| PyPI package | `pip install botscope` / `botscope[gui]` | v2.0.0 |

Network contribution stays **OFF by default**. Zero-config for local logs: no account, no cloud profile, no API key.

## What is included in a transaction (typical)

- Git repository and original BotScope source/docs (subject to agreement)
- Asserted copyright in original works (subject to counsel / chain of title)
- Branding assets created for BotScope (registration status UNKNOWN)
- Acquisition data room under `docs/acquisition/`

## What is NOT included

- Historical Apache-2.0 grants already received by third parties
- Operator-published IP range data / Cloudflare Radar data
- Third-party dependency source
- Buyer cloud accounts or secrets
- Fabricated user/revenue/census metrics (none claimed)

## Maturity

v2.0.0 on PyPI; short git history. Single human maintainer + Dependabot. See `docs/acquisition/EXECUTIVE_SUMMARY.md`.

## Technical differentiation

- Evidence-gated classification with UNKNOWN-first posture
- Federated public panels for an Internet-wide census story (local KPIs stay dataset-scoped)
- Offline-first first-run (`botscope hello`) and diagnostics (`botscope doctor`)
- Optional local GUI Observatory and live capture extras

## Transferable IP / third-party / limitations

See:

- `docs/acquisition/IP_AUDIT.md`
- `docs/acquisition/TRANSFER_MANIFEST.md`
- `docs/acquisition/BOTSCOPE_DILIGENCE.md`
- `docs/acquisition/DEPENDENCY_AUDIT.md`

## Demo path (buyer / evaluator)

Fresh machine, no secrets required for the minimal path:

```bash
pip install botscope
botscope doctor
botscope hello
botscope hello --keep-session demo.bscope
botscope access
```

With GUI extras:

```bash
pip install 'botscope[gui]'
botscope gui
```

From a clone (contributors / diligence):

```bash
git clone https://github.com/theworker02/botscope.git && cd botscope
python3 -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
botscope hello
pytest -q
```

Expected: commands exit 0; demo output is labeled **DEMO**; no fabricated Internet-wide rates. Detailed script: `docs/acquisition/BUYER_DEMO.md`. First-hour operator guide: `docs/guides/EASE_OF_ACCESS.md`.

## Handoff / evaluation

- `docs/acquisition/HANDOFF_PLAN.md`
- `docs/acquisition/BUYER_DEMO.md`
- `docs/acquisition/BUYER_DUE_DILIGENCE_CHECKLIST.md`
- `docs/acquisition/CHANGE_OF_CONTROL_CHECKLIST.md`

## Acquisition contact

GitHub [@theworker02](https://github.com/theworker02) · https://github.com/theworker02/botscope

Commercial / license questions: see root `COMMERCIAL.md` and `SUPPORT.md`.
