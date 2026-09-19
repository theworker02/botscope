# Parallel Work Ledger — BotScope v0.1 / Phase II

**Status:** IMPLEMENTED (process document)  
**Last reconciled:** 2026-09-18  
**Agents:** Agent 1 = Core Builder · Agent 2 = Parallel Multitask Expansion

## Rules

1. Prefer **new isolated modules** under `src/botscope/` over editing shared central files.
2. Before modifying any Agent-1-owned file: **re-read**, preserve their changes, merge intentionally — never blind overwrite.
3. Do **not** mass-rename, move core dirs, change public APIs, GUI framework, classifier architecture, storage engine, or package name.
4. Network contribution stays **OFF by default**. No unauthorized probing.
5. Documentation status labels must match code reality.

## Ownership table (summary)

| Area | Owner | Status |
|------|-------|--------|
| api/classify/identity/ingest/normalize/storage/statistics/reports/signatures/privacy/network/native | A1 | IMPLEMENTED |
| cli/ | Shared | PARTIAL — dispatcher + core cmds filled by A2 when missing |
| provenance/quality/compare/research/query/annotations/notebook/diagnostics/plugins.sdk/capabilities/botcard/manifests/demo | A2 | IMPLEMENTED / EXPERIMENTAL where noted |
| capture/enrich/behavior/flows/estimation/datasets | A2 | PARTIAL / EXPERIMENTAL / RESEARCH |
| gui/ | Shared | EXPERIMENTAL |
| docs/, .github/, examples/, tests/ (A2 modules), scripts/ | A2 | IMPLEMENTED / PARTIAL |

## Reconciliation log

| Date | Observation |
|------|-------------|
| 2026-09-18 | Initial: A1 core present; no docs/tests/cli/examples. |
| 2026-09-18 | Empty-folder remediation: filled cli/demo/gui/notebook/plugins.sdk + capture/enrich/behavior/flows/estimation/datasets; examples + tests + GitHub community files. `pytest` 16 passed; `repo_audit` PASS; 0 empty dirs remaining under audited trees. |
