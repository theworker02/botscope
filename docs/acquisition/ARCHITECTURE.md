# Architecture — BotScope

See also repository root architecture docs where present (`ARCHITECTURE.md`, `docs/`, `README.md`).

## Stack

Python >=3.10 (Hatchling); optional PySide6 GUI

## Deployment

pip install; CLI `botscope`; optional GUI; optional Cloudflare Radar token.

## Summary

Internet-wide bot traffic census / local analyzer: federates public crawler IP panels and optional CDN estimates; local log/session analysis and Qt Observatory.

## Boundaries

- Third-party runtimes, cloud providers, and SDKs are **dependencies**, not owned assets.
- Project-specific diligence: [`BOTSCOPE_DILIGENCE.md`](./BOTSCOPE_DILIGENCE.md).

Buyer should walk architecture with the handoff plan ([HANDOFF_PLAN.md](./HANDOFF_PLAN.md)).
