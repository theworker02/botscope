# Dependency Audit — BotScope

**Date:** 2026-09-21

## Summary

click, pydantic, rich, platformdirs, packaging; optional PySide6, scapy, numpy/sklearn, duckdb, httpx. No lockfile. No GPL/AGPL declared in core deps.

## Third-party content (non-package)

Public operator IP range JSON (Google, Bing, OpenAI, etc.) under operator terms; optional Cloudflare Radar API; synthetic demo datasets only.

## Copyleft

No GPL/AGPL/LGPL **declared as core direct dependencies** in the audits performed.
Optional GUI stacks (e.g. PySide6/Qt) may introduce LGPL obligations if redistributed — **REQUIRES_LEGAL_REVIEW** where applicable (OpenDashCAN/BotScope GUI extras).

## SBOM status

Formal CycloneDX/SPDX SBOM may be partial or absent. Buyer should regenerate SBOM at transfer.

## Obligations

- Retain dependency license notices on redistribution.
- Do not relicense third-party code.
- Cloudflare / operator / vendor terms are separate contracts — **REQUIRES_PERMISSION** for some commercial redistributions of derived data.
