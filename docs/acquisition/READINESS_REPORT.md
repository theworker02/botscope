# Acquisition Readiness Report — BotScope

**Date:** 2026-09-21  
**No numeric score.** Statuses reflect evidence available in-repo and this program.

| Section | Status | Notes |
|---------|--------|-------|
| BUILD | READY | Verified in TEST_EVIDENCE.md (this program) |
| TESTS | READY | Verified in TEST_EVIDENCE.md (this program) |
| SECURITY | READY_WITH_DISCLOSURE | No SECRET_FOUND. Test placeholders for Cloudflare tokens only. |
| DOCUMENTATION | READY_WITH_DISCLOSURE | Data room created this program |
| IP OWNERSHIP | REQUIRES_LEGAL_REVIEW | LICENSE: theworker02. Historical Apache: 'BotScope Contributors'. pyproject authors still 'BotScope … |
| LICENSE CLARITY | READY_WITH_DISCLOSURE | Current LICENSE clear; history documented; ETW revocation language corrected if applicable |
| DEPENDENCIES | READY_WITH_DISCLOSURE | click, pydantic, rich, platformdirs, packaging; optional PySide6, scapy, numpy/sklearn, duckdb, http… |
| THIRD-PARTY ASSETS | READY_WITH_DISCLOSURE / REQUIRES_LEGAL_REVIEW | See diligence |
| DATA RIGHTS | REQUIRES_LEGAL_REVIEW | Especially federated/operator/vendor data |
| REPRODUCIBILITY | READY_WITH_DISCLOSURE | BUYER_DEMO provided |
| TRANSFERABILITY | READY_WITH_DISCLOSURE | See TRANSFER_MANIFEST |
| OPERATIONS | READY_WITH_DISCLOSURE | Handoff + ops docs |
| BUYER DEMO | READY_WITH_DISCLOSURE | Commands verified where stack runnable; see TEST_EVIDENCE |
| KNOWN LIABILITIES | READY_WITH_DISCLOSURE | See DISCLOSURE_SCHEDULE |

## Blockers

### Before outreach
- Stale Apache references in CITATION/export (fixed this program)
- No dependency SBOM lockfile

### Before diligence
- Operator data redistribution rights for commercial sale
- Apache→proprietary transition
- Dataset fixture license clarity

### Before signing
- Formal IP assignment
- Data rights schedule for federated sources

### Before closing
- PyPI project transfer
- Credential rotation for any Radar tokens
- SPA/APA
