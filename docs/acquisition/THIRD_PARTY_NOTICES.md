# Third-Party Notices — BotScope

**Date:** 2026-09-21

This file summarizes third-party materials observed in-tree. It is **not** a complete SBOM.

## Package dependencies

click, pydantic, rich, platformdirs, packaging; optional PySide6, scapy, numpy/sklearn, duckdb, httpx. No lockfile. No GPL/AGPL declared in core deps.

Retain upstream license texts when redistributing binaries or bundled node_modules/site-packages.

## Non-package third-party materials

Public operator IP range JSON (Google, Bing, OpenAI, etc.) under operator terms; optional Cloudflare Radar API; synthetic demo datasets only.

## Trademarks

Third-party marks referenced in docs remain owned by their respective owners. Project disclaimers (where present) should be preserved.

## Action items

- [ ] Regenerate machine-readable SBOM at closing
- [ ] Confirm Qt/PySide6 redistribution path if shipping GUI wheels — **REQUIRES_LEGAL_REVIEW**
- [ ] Confirm any vendored trees still carry upstream LICENSE/NOTICE
